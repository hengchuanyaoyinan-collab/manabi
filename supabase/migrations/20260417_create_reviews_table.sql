-- 20260417_create_reviews_table.sql
-- reviews テーブル + 信用スコア自動再計算トリガー
-- Supabase MCP 経由で本番プロジェクトに適用済み。

create table if not exists public.reviews (
  id uuid primary key default gen_random_uuid(),
  booking_id uuid references public.bookings(id) on delete cascade,
  reviewer_id uuid references public.profiles(id) on delete cascade,
  reviewee_id uuid references public.profiles(id) on delete cascade,
  rating int not null check (rating >= 1 and rating <= 5),
  comment text,
  created_at timestamptz default now()
);

create unique index if not exists reviews_booking_reviewer_key
  on public.reviews (booking_id, reviewer_id);

alter table public.reviews enable row level security;

drop policy if exists "reviews_select_all" on public.reviews;
create policy "reviews_select_all" on public.reviews for select using (true);

drop policy if exists "reviews_insert_reviewer" on public.reviews;
create policy "reviews_insert_reviewer" on public.reviews for insert
  with check (auth.uid() = reviewer_id);

drop policy if exists "reviews_update_reviewer" on public.reviews;
create policy "reviews_update_reviewer" on public.reviews for update
  using (auth.uid() = reviewer_id) with check (auth.uid() = reviewer_id);

alter publication supabase_realtime add table public.reviews;

-- 信用スコア再計算関数
-- score = 10 + (avg_rating * 10) + (review_count * 3) + (sessions * 2)
create or replace function public.recalculate_score(target_user_id uuid)
returns void language plpgsql security definer set search_path = public as $$
declare
  avg_r numeric;
  rev_count int;
  sess_count int;
  new_score int;
begin
  select coalesce(avg(rating), 0), count(*)
    into avg_r, rev_count
    from reviews where reviewee_id = target_user_id;

  select count(*) into sess_count
    from bookings
    where (student_id = target_user_id or teacher_id = target_user_id)
      and status = 'confirmed';

  new_score := 10 + round(avg_r * 10) + (rev_count * 3) + (sess_count * 2);

  update profiles set score = new_score where id = target_user_id;
end;
$$;

-- レビュー挿入時に reviewee のスコアを自動更新
create or replace function public.on_review_inserted()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  perform recalculate_score(NEW.reviewee_id);
  return NEW;
end;
$$;

drop trigger if exists trg_review_inserted on public.reviews;
create trigger trg_review_inserted
  after insert on public.reviews
  for each row execute function public.on_review_inserted();
