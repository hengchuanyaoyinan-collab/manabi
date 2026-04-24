// supabase/functions/process-payout/index.ts
//
// Stripe Connect を使った講師への支払い (Payout) を管理する Edge Function。
//
// 4 つのアクションを POST の JSON body で受け付ける:
//   action: 'onboard'   — Connect Express アカウント作成 & オンボーディングURL発行
//   action: 'dashboard' — Express ダッシュボードへのログインリンク発行
//   action: 'payout'    — 完了済み予約の報酬を講師へ送金 (Transfer)
//   action: 'status'    — 講師の Connect アカウント状態・残高を返却
//
// 必要な環境変数 (Supabase Dashboard → Project Settings → Functions → Secrets):
//   STRIPE_SECRET_KEY         : sk_test_... または sk_live_...
//   PUBLIC_SITE_URL           : 例 https://manabi.example.com (リダイレクト先URL用)
//   SUPABASE_URL              : Supabase 側で自動注入される
//   SUPABASE_SERVICE_ROLE_KEY : Supabase 側で自動注入される
//
// verify_jwt = true でデプロイ。
// 呼び出し元は Authorization: Bearer <user JWT> を必ず付けること。

import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import Stripe from 'npm:stripe@17.5.0';
import { createClient } from 'jsr:@supabase/supabase-js@2';

/* ---------- env ---------- */
const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY')!;
const PUBLIC_SITE_URL = Deno.env.get('PUBLIC_SITE_URL') ?? '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

/* ---------- clients ---------- */
const stripe = new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2024-12-18.acacia' });

/** Platform fee rate — the platform keeps 5 % of each payment. */
const FEE_RATE = 0.05;

/* ---------- CORS ---------- */
const ALLOWED_ORIGINS = [
  'https://manabi-bay.vercel.app',
  PUBLIC_SITE_URL,
].filter(Boolean);

function getAllowOrigin(req: Request): string {
  const origin = req.headers.get('origin') ?? '';
  return ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0] || '';
}

function makeCors(req: Request) {
  return {
    'Access-Control-Allow-Origin': getAllowOrigin(req),
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
  };
}

function json(req: Request, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...makeCors(req) },
  });
}

/* ---------- handler ---------- */
Deno.serve(async (req) => {
  const corsHeaders = makeCors(req);

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return json(req, { error: 'method_not_allowed' }, 405);
  }

  try {
    // --- Auth: JWT を Supabase で検証 ---
    const authHeader = req.headers.get('Authorization') ?? '';
    const jwt = authHeader.replace(/^Bearer\s+/i, '');
    if (!jwt) return json(req, { error: 'missing_authorization' }, 401);

    const userClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
      global: { headers: { Authorization: `Bearer ${jwt}` } },
    });
    const { data: userData, error: userErr } = await userClient.auth.getUser(jwt);
    if (userErr || !userData?.user) return json(req, { error: 'invalid_token' }, 401);
    const user = userData.user;

    // service role client for privileged operations
    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    const body = await req.json().catch(() => ({}));
    const { action } = body ?? {};

    switch (action) {
      case 'onboard':
        return await handleOnboard(req, user, admin);
      case 'dashboard':
        return await handleDashboard(req, user, admin);
      case 'payout':
        return await handlePayout(req, user, admin, body);
      case 'status':
        return await handleStatus(req, user, admin);
      default:
        return json(req, { error: 'invalid_action', message: '有効な action を指定してください' }, 400);
    }
  } catch (e) {
    console.error('process-payout error', e);
    return json(req, { error: 'internal_error', message: '処理中にエラーが発生しました' }, 500);
  }
});

/* =================================================================
 *  action: 'onboard'
 *  Stripe Connect Express アカウントを作成し、オンボーディングリンクを返す。
 *  既にアカウントがある場合は新しいアカウントリンクだけ返す。
 * ================================================================= */
async function handleOnboard(
  req: Request,
  user: { id: string; email?: string },
  admin: ReturnType<typeof createClient>,
) {
  const siteUrl = PUBLIC_SITE_URL || 'https://manabi-bay.vercel.app';

  // 既存の connect アカウントを確認
  const { data: profile, error: profileErr } = await admin
    .from('profiles')
    .select('stripe_connect_id')
    .eq('id', user.id)
    .single();

  if (profileErr) {
    console.error('profile lookup error:', profileErr.message);
    return json(req, { error: 'profile_not_found', message: 'プロフィールが見つかりません' }, 404);
  }

  let accountId: string = profile.stripe_connect_id ?? '';

  if (!accountId) {
    // 新規 Connect Express アカウントを作成
    const account = await stripe.accounts.create({
      type: 'express',
      country: 'JP',
      email: user.email ?? undefined,
      capabilities: {
        card_payments: { requested: true },
        transfers: { requested: true },
      },
      metadata: { manabi_user_id: user.id },
    });
    accountId = account.id;

    // profiles テーブルに保存
    const { error: updateErr } = await admin
      .from('profiles')
      .update({ stripe_connect_id: accountId })
      .eq('id', user.id);

    if (updateErr) {
      console.error('profile update error:', updateErr.message);
      return json(req, { error: 'profile_update_failed', message: 'プロフィールの更新に失敗しました' }, 500);
    }
  }

  // オンボーディング用のアカウントリンクを発行
  const accountLink = await stripe.accountLinks.create({
    account: accountId,
    refresh_url: `${siteUrl}/dashboard/payout?refresh=true`,
    return_url: `${siteUrl}/dashboard/payout?onboard=complete`,
    type: 'account_onboarding',
  });

  return json(req, { url: accountLink.url, account_id: accountId });
}

/* =================================================================
 *  action: 'dashboard'
 *  Express ダッシュボードへのログインリンクを返す。
 * ================================================================= */
async function handleDashboard(
  req: Request,
  user: { id: string },
  admin: ReturnType<typeof createClient>,
) {
  const { data: profile, error: profileErr } = await admin
    .from('profiles')
    .select('stripe_connect_id')
    .eq('id', user.id)
    .single();

  if (profileErr || !profile?.stripe_connect_id) {
    return json(req, { error: 'no_connect_account', message: 'Stripe Connect アカウントが未登録です' }, 400);
  }

  const loginLink = await stripe.accounts.createLoginLink(profile.stripe_connect_id);

  return json(req, { url: loginLink.url });
}

/* =================================================================
 *  action: 'payout'
 *  完了済み予約の報酬を講師の Connect アカウントへ Transfer する。
 *  body: { action: 'payout', booking_id: '<uuid>' }
 * ================================================================= */
async function handlePayout(
  req: Request,
  user: { id: string },
  admin: ReturnType<typeof createClient>,
  body: Record<string, unknown>,
) {
  const { booking_id } = body;
  if (!booking_id || typeof booking_id !== 'string') {
    return json(req, { error: 'missing_booking_id', message: 'booking_id を指定してください' }, 400);
  }

  const uuidRe = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRe.test(booking_id)) {
    return json(req, { error: 'invalid_booking_id' }, 400);
  }

  // 予約を取得
  const { data: booking, error: bookingErr } = await admin
    .from('bookings')
    .select('id, student_id, teacher_id, status')
    .eq('id', booking_id)
    .single();

  if (bookingErr || !booking) {
    return json(req, { error: 'booking_not_found', message: '予約が見つかりません' }, 404);
  }

  // リクエスト者が講師であることを確認
  if (booking.teacher_id !== user.id) {
    return json(req, { error: 'not_teacher', message: 'この予約の講師のみが報酬を受け取れます' }, 403);
  }

  // 予約が完了済みであることを確認
  if (booking.status !== 'completed') {
    return json(req, { error: 'booking_not_completed', message: '予約が完了状態ではありません' }, 400);
  }

  // 支払い情報を取得
  const { data: payment, error: paymentErr } = await admin
    .from('payments')
    .select('id, amount, fee, currency, status, stripe_payment_intent_id')
    .eq('booking_id', booking_id)
    .eq('status', 'paid')
    .single();

  if (paymentErr || !payment) {
    return json(req, { error: 'payment_not_found', message: '支払い済みの決済情報が見つかりません' }, 404);
  }

  // 既に payout が存在しないか確認
  const { data: existingPayout } = await admin
    .from('payouts')
    .select('id')
    .eq('booking_id', booking_id)
    .limit(1)
    .maybeSingle();

  if (existingPayout) {
    return json(req, { error: 'payout_already_exists', message: 'この予約の報酬は既に送金済みです' }, 409);
  }

  // 講師の Connect アカウントを取得
  const { data: profile, error: profileErr } = await admin
    .from('profiles')
    .select('stripe_connect_id')
    .eq('id', user.id)
    .single();

  if (profileErr || !profile?.stripe_connect_id) {
    return json(req, { error: 'no_connect_account', message: 'Stripe Connect アカウントが未登録です' }, 400);
  }

  // 講師への送金額を計算 (amount - fee)
  // fee は既にプラットフォーム手数料として payments に保存されている場合はそれを使う。
  // なければ FEE_RATE で計算する。
  const platformFee = payment.fee > 0
    ? payment.fee
    : Math.round(payment.amount * FEE_RATE);
  const teacherAmount = payment.amount - platformFee;

  if (teacherAmount <= 0) {
    return json(req, { error: 'invalid_payout_amount', message: '送金額が不正です' }, 400);
  }

  // Stripe Transfer を作成
  const transfer = await stripe.transfers.create({
    amount: teacherAmount,
    currency: payment.currency || 'jpy',
    destination: profile.stripe_connect_id,
    transfer_group: `booking_${booking_id}`,
    metadata: {
      booking_id,
      payment_id: payment.id,
      teacher_id: user.id,
    },
  });

  // payouts テーブルに記録
  const { data: payout, error: payoutErr } = await admin
    .from('payouts')
    .insert({
      booking_id,
      payment_id: payment.id,
      teacher_id: user.id,
      amount: teacherAmount,
      platform_fee: platformFee,
      currency: payment.currency || 'jpy',
      stripe_transfer_id: transfer.id,
      stripe_connect_id: profile.stripe_connect_id,
      status: 'completed',
    })
    .select('id')
    .single();

  if (payoutErr) {
    console.error('payout insert error:', payoutErr.message);
    // Transfer は成功しているのでログだけ残す
    return json(req, {
      error: 'payout_record_failed',
      message: '送金は成功しましたが記録に失敗しました。サポートにご連絡ください。',
      stripe_transfer_id: transfer.id,
    }, 500);
  }

  return json(req, {
    payout_id: payout.id,
    amount: teacherAmount,
    platform_fee: platformFee,
    currency: payment.currency || 'jpy',
    stripe_transfer_id: transfer.id,
  });
}

/* =================================================================
 *  action: 'status'
 *  講師の Stripe Connect アカウント状態と残高を返す。
 * ================================================================= */
async function handleStatus(
  req: Request,
  user: { id: string },
  admin: ReturnType<typeof createClient>,
) {
  const { data: profile, error: profileErr } = await admin
    .from('profiles')
    .select('stripe_connect_id')
    .eq('id', user.id)
    .single();

  if (profileErr) {
    return json(req, { error: 'profile_not_found', message: 'プロフィールが見つかりません' }, 404);
  }

  if (!profile.stripe_connect_id) {
    return json(req, {
      has_account: false,
      onboarding_complete: false,
      balance: null,
    });
  }

  // Connect アカウントの詳細を取得
  const account = await stripe.accounts.retrieve(profile.stripe_connect_id);

  // 残高を取得
  const balance = await stripe.balance.retrieve({
    stripeAccount: profile.stripe_connect_id,
  });

  return json(req, {
    has_account: true,
    account_id: account.id,
    onboarding_complete: account.details_submitted ?? false,
    charges_enabled: account.charges_enabled ?? false,
    payouts_enabled: account.payouts_enabled ?? false,
    balance: {
      available: balance.available ?? [],
      pending: balance.pending ?? [],
    },
  });
}
