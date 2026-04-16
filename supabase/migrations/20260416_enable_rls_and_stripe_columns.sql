-- 20260416_enable_rls_and_stripe_columns.sql
-- このファイルは Supabase MCP 経由で本番プロジェクトに既に適用済みです。
-- 再現用に同等の SQL を残しています (supabase db push でローカル管理する場合に利用)。

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.bookings enable row level security;
alter table public.payments enable row level security;
alter table public.messages enable row level security;

-- profiles policies
drop policy if exists "profiles_select_all" on public.profiles;
create policy "profiles_select_all" on public.profiles for select using (true);

drop policy if exists "profiles_insert_self" on public.profiles;
create policy "profiles_insert_self" on public.profiles for insert with check (auth.uid() = id);

drop policy if exists "profiles_update_self" on public.profiles;
create policy "profiles_update_self" on public.profiles for update
  using (auth.uid() = id) with check (auth.uid() = id);

-- skills policies
drop policy if exists "skills_select_all" on public.skills;
create policy "skills_select_all" on public.skills for select using (true);

drop policy if exists "skills_insert_self" on public.skills;
create policy "skills_insert_self" on public.skills for insert with check (auth.uid() = user_id);

drop policy if exists "skills_update_self" on public.skills;
create policy "skills_update_self" on public.skills for update
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop policy if exists "skills_delete_self" on public.skills;
create policy "skills_delete_self" on public.skills for delete using (auth.uid() = user_id);

-- 旧来の許容ポリシー (always true) を除去
drop policy if exists "認証ユーザーはスキルを作成できる" on public.skills;

-- bookings policies
drop policy if exists "bookings_select_party" on public.bookings;
create policy "bookings_select_party" on public.bookings for select
  using (auth.uid() = student_id or auth.uid() = teacher_id);

drop policy if exists "bookings_insert_student" on public.bookings;
create policy "bookings_insert_student" on public.bookings for insert
  with check (auth.uid() = student_id);

drop policy if exists "bookings_update_party" on public.bookings;
create policy "bookings_update_party" on public.bookings for update
  using (auth.uid() = student_id or auth.uid() = teacher_id);

-- payments policies (read only; insert/update は service_role からのみ)
drop policy if exists "payments_select_party" on public.payments;
create policy "payments_select_party" on public.payments for select using (
  exists (
    select 1 from public.bookings b
    where b.id = payments.booking_id
      and (auth.uid() = b.student_id or auth.uid() = b.teacher_id)
  )
);

-- messages policies
drop policy if exists "messages_select_party" on public.messages;
create policy "messages_select_party" on public.messages for select
  using (auth.uid() = sender_id or auth.uid() = receiver_id);

drop policy if exists "messages_insert_sender" on public.messages;
create policy "messages_insert_sender" on public.messages for insert
  with check (auth.uid() = sender_id);

-- Stripe 連携用カラム
alter table public.payments add column if not exists stripe_session_id text;
alter table public.payments add column if not exists stripe_payment_intent_id text;
alter table public.payments add column if not exists currency text default 'jpy';
alter table public.payments add column if not exists updated_at timestamp default now();

create unique index if not exists payments_stripe_session_id_key
  on public.payments (stripe_session_id) where stripe_session_id is not null;
create index if not exists payments_booking_id_idx on public.payments (booking_id);

-- 新規登録ユーザに対して自動でプロファイル行を作成
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, name, score)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)),
    0
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
