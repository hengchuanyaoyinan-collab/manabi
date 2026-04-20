-- ============================================================
-- AI MATCHING SYSTEM SCHEMA
-- ============================================================

-- 1. Enable pgvector for embedding storage & similarity search
create extension if not exists vector with schema extensions;

-- 2. AI-analyzed teacher profiles with embeddings
create table public.ai_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade not null unique,
  embedding extensions.vector(1536),
  skills_summary text,
  teaching_strengths text[],
  experience_level text check (experience_level in ('beginner','intermediate','advanced','expert')),
  personality_tags text[],
  subject_keywords text[],
  analyzed_at timestamptz default now(),
  raw_analysis jsonb default '{}'::jsonb
);

-- 3. Enhance learning_requests with AI-structured data
alter table public.learning_requests
  add column if not exists embedding extensions.vector(1536),
  add column if not exists ai_structured jsonb default '{}'::jsonb,
  add column if not exists preferred_style text,
  add column if not exists skill_level text,
  add column if not exists urgency text default 'normal'
    check (urgency in ('low','normal','high','urgent'));

-- 4. AI match results
create table public.ai_matches (
  id uuid primary key default gen_random_uuid(),
  request_id uuid references public.learning_requests(id) on delete cascade not null,
  teacher_id uuid references public.profiles(id) on delete cascade not null,
  skill_id uuid references public.skills(id) on delete set null,
  score numeric(5,2) not null check (score >= 0 and score <= 100),
  score_breakdown jsonb not null default '{}'::jsonb,
  ai_reason text,
  status text not null default 'recommended'
    check (status in ('recommended','viewed','accepted','declined','expired','booked')),
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(request_id, teacher_id)
);

-- 5. Match feedback for learning loop
create table public.match_feedback (
  id uuid primary key default gen_random_uuid(),
  match_id uuid references public.ai_matches(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  action text not null
    check (action in ('view','click','message','book','complete','review','skip','dismiss')),
  rating int check (rating is null or (rating >= 1 and rating <= 5)),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- INDEXES
create index idx_ai_profiles_embedding
  on public.ai_profiles using hnsw (embedding extensions.vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create index idx_learning_requests_embedding
  on public.learning_requests using hnsw (embedding extensions.vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create index idx_ai_matches_request_score on public.ai_matches(request_id, score desc);
create index idx_ai_matches_teacher on public.ai_matches(teacher_id);
create index idx_ai_matches_status on public.ai_matches(status);
create index idx_match_feedback_match on public.match_feedback(match_id);
create index idx_match_feedback_action on public.match_feedback(action);

-- RLS
alter table public.ai_profiles enable row level security;
alter table public.ai_matches enable row level security;
alter table public.match_feedback enable row level security;

create policy "ai_profiles_read" on public.ai_profiles for select using (true);
create policy "ai_profiles_owner_insert" on public.ai_profiles for insert with check (auth.uid() = user_id);
create policy "ai_profiles_owner_update" on public.ai_profiles for update using (auth.uid() = user_id);

create policy "ai_matches_read" on public.ai_matches for select using (
  teacher_id = auth.uid()
  or request_id in (select id from public.learning_requests where user_id = auth.uid())
);
create policy "ai_matches_service_insert" on public.ai_matches for insert with check (true);
create policy "ai_matches_user_update" on public.ai_matches for update using (
  teacher_id = auth.uid()
  or request_id in (select id from public.learning_requests where user_id = auth.uid())
);

create policy "match_feedback_insert" on public.match_feedback for insert with check (auth.uid() = user_id);
create policy "match_feedback_read" on public.match_feedback for select using (auth.uid() = user_id);

-- Helper function: vector similarity search
create or replace function public.match_teachers(
  query_embedding extensions.vector(1536),
  match_threshold float default 0.3,
  match_count int default 20
)
returns table (user_id uuid, similarity float)
language sql stable
as $$
  select ap.user_id, 1 - (ap.embedding <=> query_embedding) as similarity
  from public.ai_profiles ap
  where ap.embedding is not null
    and 1 - (ap.embedding <=> query_embedding) > match_threshold
  order by ap.embedding <=> query_embedding
  limit match_count;
$$;
