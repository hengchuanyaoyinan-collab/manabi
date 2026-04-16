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
const PUBLIC_SITE_URL = Deno.env.get('PUBLIC_SITE_URL') ?? 'http://localhost:5173';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const stripe = new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2024-12-18.acacia' });

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return json({ error: 'method_not_allowed' }, 405);
  }

  try {
    // --- Auth: ユーザの JWT を Supabase で検証 ---
    const authHeader = req.headers.get('Authorization') ?? '';
    const jwt = authHeader.replace(/^Bearer\s+/i, '');
    if (!jwt) return json({ error: 'missing_authorization' }, 401);

    const userClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
      global: { headers: { Authorization: `Bearer ${jwt}` } },
    });
    const { data: userData, error: userErr } = await userClient.auth.getUser(jwt);
    if (userErr || !userData?.user) return json({ error: 'invalid_token' }, 401);
    const user = userData.user;

    // --- 入力 ---
    const body = await req.json().catch(() => ({}));
    const {
      teacher_name = 'manabi 先生',
      teacher_id = null,           // optional: profiles.id (uuid)
      skill_id = null,             // optional: skills.id (uuid)
      amount,                      // 必須: 円 (整数)
      fee = 0,                     // 任意: 円 (整数)
      scheduled_at = null,         // 任意: ISO8601
    } = body ?? {};

    const totalYen = Math.round(Number(amount) + Number(fee));
    if (!Number.isFinite(totalYen) || totalYen < 50) {
      return json({ error: 'invalid_amount', message: '金額は¥50以上で指定してください' }, 400);
    }

    // --- service role で booking / payment を作成 ---
    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

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
    if (bErr) return json({ error: 'booking_insert_failed', message: bErr.message }, 500);

    const { data: payment, error: pErr } = await admin
      .from('payments')
      .insert({
        booking_id: booking.id,
        amount: Number(amount),
        fee: Number(fee),
        currency: 'jpy',
        status: 'pending',
      })
      .select('id')
      .single();
    if (pErr) return json({ error: 'payment_insert_failed', message: pErr.message }, 500);

    // --- Stripe Checkout Session ---
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
      success_url: `${PUBLIC_SITE_URL}?pay=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${PUBLIC_SITE_URL}?pay=cancel`,
      metadata: {
        booking_id: booking.id,
        payment_id: payment.id,
        student_id: user.id,
        teacher_name,
      },
    });

    await admin
      .from('payments')
      .update({ stripe_session_id: session.id, updated_at: new Date().toISOString() })
      .eq('id', payment.id);

    return json({ url: session.url, session_id: session.id, booking_id: booking.id });
  } catch (e) {
    console.error('create-checkout-session error', e);
    return json({ error: 'internal_error', message: String(e?.message ?? e) }, 500);
  }
});

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...corsHeaders },
  });
}
