// supabase/functions/create-checkout-session/index.ts
//
// Stripe Checkout Session を作成して URL を返す Edge Function。
//
// クライアント (manabi のブラウザ) は Supabase の access_token を Authorization
// ヘッダにつけて呼び出す。サーバ側で JWT を検証し、bookings / payments を
// 作成したうえで Stripe Checkout Session を発行する。
//
// 必要な環境変数 (Supabase Dashboard → Project Settings → Functions → Secrets):
//   STRIPE_SECRET_KEY          : sk_test_... または sk_live_...
//   STRIPE_PRICE_PRODUCT_ID    : prod_ULXjPQg07k5Uy7  (動的金額に使う商品ID)
//   PUBLIC_SITE_URL            : 例 https://manabi.example.com  (戻り先URL用)
//   SUPABASE_URL               : Supabase 側で自動注入される
//   SUPABASE_SERVICE_ROLE_KEY  : Supabase 側で自動注入される
//
// なお verify_jwt は true でデプロイされるため、
// 呼び出し元が Authorization: Bearer <user JWT> を必ず付ける必要がある。

import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import Stripe from 'npm:stripe@17.5.0';
import { createClient } from 'jsr:@supabase/supabase-js@2';

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY')!;
const STRIPE_PRICE_PRODUCT_ID = Deno.env.get('STRIPE_PRICE_PRODUCT_ID')!;
const PUBLIC_SITE_URL = Deno.env.get('PUBLIC_SITE_URL') ?? '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const stripe = new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2024-12-18.acacia' });

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

Deno.serve(async (req) => {
  const corsHeaders = makeCors(req);

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return json(req, { error: 'method_not_allowed' }, 405);
  }

  try {
    // --- Auth: ユーザの JWT を Supabase で検証 ---
    const authHeader = req.headers.get('Authorization') ?? '';
    const jwt = authHeader.replace(/^Bearer\s+/i, '');
    if (!jwt) return json(req, { error: 'missing_authorization' }, 401);

    const userClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
      global: { headers: { Authorization: `Bearer ${jwt}` } },
    });
    const { data: userData, error: userErr } = await userClient.auth.getUser(jwt);
    if (userErr || !userData?.user) return json(req, { error: 'invalid_token' }, 401);
    const user = userData.user;

    const siteUrl = PUBLIC_SITE_URL || 'https://manabi-bay.vercel.app';

    // --- 入力 ---
    const body = await req.json().catch(() => ({}));
    const {
      teacher_name = 'manabi 先生',
      teacher_id = null,           // optional: profiles.id (uuid)
      skill_id = null,             // optional: skills.id (uuid)
      amount,                      // 必須: 円 (整数)
      fee = 0,                     // 任意: 円 (整数)
      scheduled_at = null,         // 任意: ISO8601
      booking_id = null,           // optional: existing booking id
    } = body ?? {};

    const totalYen = Math.round(Number(amount) + Number(fee));
    if (!Number.isFinite(totalYen) || totalYen < 50) {
      return json(req, { error: 'invalid_amount', message: '金額は¥50以上で指定してください' }, 400);
    }
    if (totalYen > 1_000_000) {
      return json(req, { error: 'invalid_amount', message: '金額は¥1,000,000以下で指定してください' }, 400);
    }

    const uuidRe = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (teacher_id && !uuidRe.test(teacher_id)) {
      return json(req, { error: 'invalid_teacher_id' }, 400);
    }
    if (skill_id && !uuidRe.test(skill_id)) {
      return json(req, { error: 'invalid_skill_id' }, 400);
    }
    if (booking_id && !uuidRe.test(booking_id)) {
      return json(req, { error: 'invalid_booking_id' }, 400);
    }
    if (scheduled_at) {
      const d = new Date(scheduled_at);
      if (isNaN(d.getTime())) return json(req, { error: 'invalid_scheduled_at' }, 400);
    }

    if (teacher_id && teacher_id === user.id) {
      return json(req, { error: 'self_booking', message: '自分自身への予約はできません' }, 400);
    }

    // --- service role で booking / payment を作成 ---
    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    // サーバ側で価格を再検証（クライアント側の価格改ざんを防止）
    if (skill_id) {
      const { data: skill, error: skillErr } = await admin
        .from('skills')
        .select('price_min, user_id')
        .eq('id', skill_id)
        .single();
      if (skillErr || !skill) {
        return json(req, { error: 'skill_not_found', message: '指定されたスキルが見つかりません' }, 404);
      }
      if (teacher_id && skill.user_id !== teacher_id) {
        return json(req, { error: 'skill_teacher_mismatch', message: 'スキルと講師が一致しません' }, 400);
      }
      if (Number(amount) < skill.price_min) {
        return json(req, { error: 'amount_below_minimum', message: `金額はスキルの最低単価(¥${skill.price_min.toLocaleString()})以上にしてください` }, 400);
      }
    }

    let bookingId = booking_id;
    if (!bookingId) {
      const { data: booking, error: bErr } = await admin
        .from('bookings')
        .insert({
          student_id: user.id,
          teacher_id,
          skill_id,
          price: totalYen,
          scheduled_at,
          status: 'pending',
        })
        .select('id')
        .single();
      if (bErr) {
        console.error('booking insert error:', bErr.message);
        return json(req, { error: 'booking_insert_failed', message: '予約の作成に失敗しました' }, 500);
      }
      bookingId = booking.id;
    }

    const { data: payment, error: pErr } = await admin
      .from('payments')
      .insert({
        booking_id: bookingId,
        amount: Number(amount),
        fee: Number(fee),
        currency: 'jpy',
        status: 'pending',
      })
      .select('id')
      .single();
    if (pErr) {
      console.error('payment insert error:', pErr.message);
      return json(req, { error: 'payment_insert_failed', message: '決済情報の作成に失敗しました' }, 500);
    }

    // --- Stripe Checkout Session ---
    const idempotencyKey = `checkout_${bookingId}_${payment.id}`;
    const session = await stripe.checkout.sessions.create({
      mode: 'payment',
      payment_method_types: ['card'],
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: 'jpy',
            unit_amount: totalYen,
            product: STRIPE_PRICE_PRODUCT_ID,
          },
        },
      ],
      customer_email: user.email ?? undefined,
      success_url: `${siteUrl}?pay=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${siteUrl}?pay=cancel`,
      metadata: {
        booking_id: bookingId,
        payment_id: payment.id,
        student_id: user.id,
        teacher_name,
      },
    }, { idempotencyKey });

    await admin
      .from('payments')
      .update({ stripe_session_id: session.id, updated_at: new Date().toISOString() })
      .eq('id', payment.id);

    return json(req, { url: session.url, session_id: session.id, booking_id: bookingId });
  } catch (e) {
    console.error('create-checkout-session error', e);
    return json(req, { error: 'internal_error', message: '決済処理中にエラーが発生しました' }, 500);
  }
});

function json(req: Request, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...makeCors(req) },
  });
}
