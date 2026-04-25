// supabase/functions/stripe-webhook/index.ts
//
// Stripe からのイベント (checkout.session.completed など) を受けて
// payments / bookings テーブルを更新する Edge Function。
//
// 必要な環境変数 (Supabase Dashboard → Project Settings → Functions → Secrets):
//   STRIPE_SECRET_KEY          : sk_test_... または sk_live_...
//   STRIPE_WEBHOOK_SECRET      : whsec_... (Stripe Dashboard でエンドポイント作成時に発行)
//   SUPABASE_URL               : Supabase 側で自動注入される
//   SUPABASE_SERVICE_ROLE_KEY  : Supabase 側で自動注入される
//
// この関数は Stripe からの呼び出しを受け付けるため、verify_jwt = false で
// デプロイすること (代わりに Stripe-Signature ヘッダで検証する)。

import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import Stripe from 'npm:stripe@17.5.0';
import { createClient } from 'jsr:@supabase/supabase-js@2';

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY')!;
const STRIPE_WEBHOOK_SECRET = Deno.env.get('STRIPE_WEBHOOK_SECRET')!;
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

const stripe = new Stripe(STRIPE_SECRET_KEY, { apiVersion: '2024-12-18.acacia' });
const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

Deno.serve(async (req) => {
  if (req.method !== 'POST') {
    return new Response('method_not_allowed', { status: 405 });
  }

  const sig = req.headers.get('Stripe-Signature');
  if (!sig) return new Response('missing_signature', { status: 400 });

  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    event = await stripe.webhooks.constructEventAsync(
      rawBody,
      sig,
      STRIPE_WEBHOOK_SECRET,
    );
  } catch (err) {
    console.error('Stripe signature verification failed', err);
    return new Response('signature_invalid', { status: 400 });
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        const paymentId = session.metadata?.payment_id ?? null;
        const bookingId = session.metadata?.booking_id ?? null;

        if (paymentId) {
          await admin
            .from('payments')
            .update({
              status: 'paid',
              stripe_payment_intent_id: typeof session.payment_intent === 'string'
                ? session.payment_intent
                : session.payment_intent?.id ?? null,
              updated_at: new Date().toISOString(),
            })
            .eq('id', paymentId);
        }
        if (bookingId) {
          await admin
            .from('bookings')
            .update({ status: 'confirmed' })
            .eq('id', bookingId);
        }
        break;
      }

      case 'checkout.session.expired':
      case 'checkout.session.async_payment_failed': {
        const session = event.data.object as Stripe.Checkout.Session;
        const paymentId = session.metadata?.payment_id ?? null;
        if (paymentId) {
          await admin
            .from('payments')
            .update({ status: 'failed', updated_at: new Date().toISOString() })
            .eq('id', paymentId);
        }
        break;
      }

      case 'charge.refunded':
      case 'refund.created': {
        const obj = event.data.object as Stripe.Charge | Stripe.Refund;
        const paymentIntent = (obj as Stripe.Charge).payment_intent
          ?? (obj as Stripe.Refund).payment_intent;
        if (typeof paymentIntent === 'string') {
          await admin
            .from('payments')
            .update({ status: 'refunded', updated_at: new Date().toISOString() })
            .eq('stripe_payment_intent_id', paymentIntent);
        }
        break;
      }

      case 'charge.dispute.created': {
        const dispute = event.data.object as Stripe.Dispute;
        const pi = typeof dispute.payment_intent === 'string'
          ? dispute.payment_intent
          : dispute.payment_intent?.id ?? null;
        if (pi) {
          await admin
            .from('payments')
            .update({ status: 'disputed', updated_at: new Date().toISOString() })
            .eq('stripe_payment_intent_id', pi);
        }
        console.warn('Dispute received:', dispute.id, 'PI:', pi);
        break;
      }

      case 'charge.dispute.closed': {
        const dispute = event.data.object as Stripe.Dispute;
        const pi = typeof dispute.payment_intent === 'string'
          ? dispute.payment_intent
          : dispute.payment_intent?.id ?? null;
        if (pi) {
          const newStatus = dispute.status === 'won' ? 'paid' : 'refunded';
          await admin
            .from('payments')
            .update({ status: newStatus, updated_at: new Date().toISOString() })
            .eq('stripe_payment_intent_id', pi);
        }
        break;
      }

      default:
        // 対応しないイベントは 200 で受け流す
        break;
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (e) {
    console.error('webhook handler error', e);
    return new Response('handler_error', { status: 500 });
  }
});
