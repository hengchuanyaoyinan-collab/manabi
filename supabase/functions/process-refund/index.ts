// supabase/functions/process-refund/index.ts
//
// 返金リクエストの作成・承認・却下・一覧を行う Edge Function。
//
// POST JSON body: { action: 'request_refund' | 'approve_refund' | 'reject_refund' | 'list', ... }
//
// 必要な環境変数:
//   STRIPE_SECRET_KEY         : sk_test_... または sk_live_...
//   PUBLIC_SITE_URL           : 例 https://manabi.example.com
//   SUPABASE_URL              : Supabase 側で自動注入
//   SUPABASE_SERVICE_ROLE_KEY : Supabase 側で自動注入
//
// verify_jwt = true — Authorization: Bearer <user JWT> が必須。

import 'jsr:@supabase/functions-js/edge-runtime.d.ts';
import Stripe from 'npm:stripe@17.5.0';
import { createClient } from 'jsr:@supabase/supabase-js@2';

const STRIPE_SECRET_KEY = Deno.env.get('STRIPE_SECRET_KEY')!;
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

function json(req: Request, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...makeCors(req) },
  });
}

// ---------------------------------------------------------------------------
// Auth helper — validates JWT and returns the authenticated user
// ---------------------------------------------------------------------------
async function getAuthUser(req: Request) {
  const authHeader = req.headers.get('Authorization') ?? '';
  const jwt = authHeader.replace(/^Bearer\s+/i, '');
  if (!jwt) return null;

  const userClient = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    global: { headers: { Authorization: `Bearer ${jwt}` } },
  });
  const { data, error } = await userClient.auth.getUser(jwt);
  if (error || !data?.user) return null;
  return data.user;
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------
Deno.serve(async (req) => {
  const corsHeaders = makeCors(req);

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }
  if (req.method !== 'POST') {
    return json(req, { error: 'method_not_allowed' }, 405);
  }

  try {
    const user = await getAuthUser(req);
    if (!user) return json(req, { error: 'unauthorized' }, 401);

    const body = await req.json().catch(() => ({}));
    const { action } = body ?? {};

    const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

    switch (action) {
      case 'request_refund':
        return await handleRequestRefund(req, admin, user, body);
      case 'approve_refund':
        return await handleApproveRefund(req, admin, user, body);
      case 'reject_refund':
        return await handleRejectRefund(req, admin, user, body);
      case 'list':
        return await handleList(req, admin, user);
      default:
        return json(req, { error: 'invalid_action', message: 'action は request_refund / approve_refund / reject_refund / list のいずれかを指定してください' }, 400);
    }
  } catch (e) {
    console.error('process-refund error', e);
    return json(req, { error: 'internal_error', message: '返金処理中にエラーが発生しました' }, 500);
  }
});

// ---------------------------------------------------------------------------
// action: request_refund
// ---------------------------------------------------------------------------
async function handleRequestRefund(
  req: Request,
  admin: ReturnType<typeof createClient>,
  user: { id: string },
  body: Record<string, unknown>,
) {
  const { booking_id, reason, detail } = body;

  if (!booking_id || typeof booking_id !== 'string') {
    return json(req, { error: 'missing_booking_id' }, 400);
  }

  // Fetch the booking
  const { data: booking, error: bErr } = await admin
    .from('bookings')
    .select('id, student_id, teacher_id, status')
    .eq('id', booking_id)
    .single();
  if (bErr || !booking) {
    return json(req, { error: 'booking_not_found' }, 404);
  }

  // Must be the student of the booking
  if (booking.student_id !== user.id) {
    return json(req, { error: 'forbidden', message: '自分の予約のみ返金リクエストできます' }, 403);
  }

  // Booking must be confirmed (not yet completed)
  if (booking.status !== 'confirmed') {
    return json(req, { error: 'invalid_booking_status', message: '確定済みの予約のみ返金リクエストできます' }, 400);
  }

  // Payment must be paid
  const { data: payment, error: pErr } = await admin
    .from('payments')
    .select('id, status')
    .eq('booking_id', booking_id)
    .eq('status', 'paid')
    .limit(1)
    .single();
  if (pErr || !payment) {
    return json(req, { error: 'payment_not_paid', message: '支払い済みの決済が見つかりません' }, 400);
  }

  // Create the refund request
  const { data: refundReq, error: rErr } = await admin
    .from('refund_requests')
    .insert({
      booking_id,
      payment_id: payment.id,
      student_id: user.id,
      teacher_id: booking.teacher_id,
      reason: reason ?? null,
      detail: detail ?? null,
      status: 'pending',
    })
    .select('id')
    .single();
  if (rErr) {
    console.error('refund_request insert error:', rErr.message);
    return json(req, { error: 'refund_request_failed', message: '返金リクエストの作成に失敗しました' }, 500);
  }

  return json(req, { success: true, refund_request_id: refundReq.id });
}

// ---------------------------------------------------------------------------
// action: approve_refund
// ---------------------------------------------------------------------------
async function handleApproveRefund(
  req: Request,
  admin: ReturnType<typeof createClient>,
  user: { id: string },
  body: Record<string, unknown>,
) {
  const { refund_request_id } = body;

  if (!refund_request_id || typeof refund_request_id !== 'string') {
    return json(req, { error: 'missing_refund_request_id' }, 400);
  }

  // Fetch the refund request
  const { data: refundReq, error: rErr } = await admin
    .from('refund_requests')
    .select('id, booking_id, payment_id, teacher_id, status')
    .eq('id', refund_request_id)
    .single();
  if (rErr || !refundReq) {
    return json(req, { error: 'refund_request_not_found' }, 404);
  }

  if (refundReq.status !== 'pending') {
    return json(req, { error: 'refund_request_not_pending', message: 'この返金リクエストは既に処理済みです' }, 400);
  }

  // Authorize: must be the teacher of the booking OR an admin
  const isTeacher = refundReq.teacher_id === user.id;
  let isAdmin = false;
  if (!isTeacher) {
    const { data: profile } = await admin
      .from('profiles')
      .select('role')
      .eq('id', user.id)
      .single();
    isAdmin = profile?.role === 'admin';
  }
  if (!isTeacher && !isAdmin) {
    return json(req, { error: 'forbidden', message: '承認権限がありません' }, 403);
  }

  // Fetch the payment to get the Stripe payment intent ID
  const { data: payment, error: pErr } = await admin
    .from('payments')
    .select('id, stripe_payment_intent_id')
    .eq('id', refundReq.payment_id)
    .single();
  if (pErr || !payment) {
    return json(req, { error: 'payment_not_found' }, 404);
  }
  if (!payment.stripe_payment_intent_id) {
    return json(req, { error: 'missing_payment_intent', message: 'Stripe の決済情報が見つかりません' }, 400);
  }

  // Execute the Stripe refund
  try {
    await stripe.refunds.create({
      payment_intent: payment.stripe_payment_intent_id,
    });
  } catch (stripeErr: unknown) {
    const message = stripeErr instanceof Error ? stripeErr.message : 'Unknown Stripe error';
    console.error('Stripe refund error:', message);
    return json(req, { error: 'stripe_refund_failed', message: 'Stripe での返金処理に失敗しました' }, 502);
  }

  // Update payment status to refunded
  await admin
    .from('payments')
    .update({ status: 'refunded', updated_at: new Date().toISOString() })
    .eq('id', refundReq.payment_id);

  // Update booking status to cancelled
  await admin
    .from('bookings')
    .update({ status: 'cancelled' })
    .eq('id', refundReq.booking_id);

  // Update refund request status to approved
  await admin
    .from('refund_requests')
    .update({ status: 'approved', resolved_by: user.id, resolved_at: new Date().toISOString() })
    .eq('id', refund_request_id);

  return json(req, { success: true });
}

// ---------------------------------------------------------------------------
// action: reject_refund
// ---------------------------------------------------------------------------
async function handleRejectRefund(
  req: Request,
  admin: ReturnType<typeof createClient>,
  user: { id: string },
  body: Record<string, unknown>,
) {
  const { refund_request_id, reason } = body;

  if (!refund_request_id || typeof refund_request_id !== 'string') {
    return json(req, { error: 'missing_refund_request_id' }, 400);
  }

  // Fetch the refund request
  const { data: refundReq, error: rErr } = await admin
    .from('refund_requests')
    .select('id, teacher_id, status')
    .eq('id', refund_request_id)
    .single();
  if (rErr || !refundReq) {
    return json(req, { error: 'refund_request_not_found' }, 404);
  }

  if (refundReq.status !== 'pending') {
    return json(req, { error: 'refund_request_not_pending', message: 'この返金リクエストは既に処理済みです' }, 400);
  }

  // Authorize: must be the teacher or admin
  const isTeacher = refundReq.teacher_id === user.id;
  let isAdmin = false;
  if (!isTeacher) {
    const { data: profile } = await admin
      .from('profiles')
      .select('role')
      .eq('id', user.id)
      .single();
    isAdmin = profile?.role === 'admin';
  }
  if (!isTeacher && !isAdmin) {
    return json(req, { error: 'forbidden', message: '却下権限がありません' }, 403);
  }

  // Update refund request status to rejected
  await admin
    .from('refund_requests')
    .update({
      status: 'rejected',
      reject_reason: reason ?? null,
      resolved_by: user.id,
      resolved_at: new Date().toISOString(),
    })
    .eq('id', refund_request_id);

  return json(req, { success: true });
}

// ---------------------------------------------------------------------------
// action: list
// ---------------------------------------------------------------------------
async function handleList(
  req: Request,
  admin: ReturnType<typeof createClient>,
  user: { id: string },
) {
  // Return refund requests where the user is either the student or the teacher.
  // Admins see all requests.
  const { data: profile } = await admin
    .from('profiles')
    .select('role')
    .eq('id', user.id)
    .single();
  const isAdmin = profile?.role === 'admin';

  let query = admin
    .from('refund_requests')
    .select('*, bookings:booking_id(id, skill_id, price, scheduled_at), payments:payment_id(id, amount, fee, currency)')
    .order('created_at', { ascending: false });

  if (!isAdmin) {
    query = query.or(`student_id.eq.${user.id},teacher_id.eq.${user.id}`);
  }

  const { data, error } = await query;
  if (error) {
    console.error('refund_requests list error:', error.message);
    return json(req, { error: 'list_failed', message: '返金リクエスト一覧の取得に失敗しました' }, 500);
  }

  return json(req, { success: true, refund_requests: data });
}
