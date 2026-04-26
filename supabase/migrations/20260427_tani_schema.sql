-- =====================================================================
-- 20260427_tani_schema.sql — DRAFT, NOT YET APPLIED
-- =====================================================================
-- 単位取得レシピ・プラットフォーム (仮称: Tan-i) のスキーマ
--
-- 状態: ドラフト。レビュー後に手動で適用すること。
-- 適用前に必ず以下を確認:
--   1. 既存の Manabi スキーマと干渉しないこと
--   2. RLS ポリシーの最終確認
--   3. pgroonga / pgvector 拡張が利用可能なこと
-- =====================================================================

-- 必要な拡張機能（既に有効でなければ）
-- CREATE EXTENSION IF NOT EXISTS pgroonga;
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------
-- 大学マスタ
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_universities (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text UNIQUE NOT NULL,
    name            text NOT NULL,
    type            text NOT NULL CHECK (type IN ('correspondence', 'on-campus', 'hybrid')),
    logo_url        text,
    description     text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.tani_universities IS '大学マスタ（法政通信、放送大学など）';

-- ---------------------------------------------------------------------
-- 学部
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_faculties (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id   uuid NOT NULL REFERENCES public.tani_universities(id) ON DELETE CASCADE,
    slug            text NOT NULL,
    name            text NOT NULL,
    UNIQUE (university_id, slug)
);

-- ---------------------------------------------------------------------
-- 科目マスタ
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_subjects (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id   uuid NOT NULL REFERENCES public.tani_universities(id) ON DELETE CASCADE,
    faculty_id      uuid REFERENCES public.tani_faculties(id) ON DELETE SET NULL,
    slug            text NOT NULL,
    name            text NOT NULL,
    code            text,
    category        text CHECK (category IN ('general', 'major', 'schooling', 'media', 'thesis', 'other')),
    credits         smallint,
    difficulty_avg  numeric(3,2),  -- 投稿の集計から自動更新
    recipe_count    int DEFAULT 0,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (university_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_tani_subjects_university ON public.tani_subjects(university_id);
CREATE INDEX IF NOT EXISTS idx_tani_subjects_name_pgroonga ON public.tani_subjects USING pgroonga (name);

-- ---------------------------------------------------------------------
-- ユーザー拡張プロフィール（auth.users と1対1）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_profiles (
    id              uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name    text,
    avatar_url      text,
    university_id   uuid REFERENCES public.tani_universities(id) ON DELETE SET NULL,
    faculty_id      uuid REFERENCES public.tani_faculties(id) ON DELETE SET NULL,
    enrollment_year int,
    status          text CHECK (status IN ('in_school', 'graduated', 'dropout', 'observer')),
    bio             text,
    verified        boolean DEFAULT false,  -- 学籍確認済（任意）
    verified_at     timestamptz,
    recipe_count    int DEFAULT 0,
    helpful_received int DEFAULT 0,
    badges          jsonb DEFAULT '[]'::jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- レシピ（コアテーブル）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_recipes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text NOT NULL,
    author_id       uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    subject_id      uuid NOT NULL REFERENCES public.tani_subjects(id) ON DELETE RESTRICT,

    title           text NOT NULL,
    summary         text,                         -- 2-3 行の要約
    body_md         text,                         -- 本文 markdown

    -- 構造化メタデータ
    difficulty      smallint CHECK (difficulty BETWEEN 1 AND 5),
    duration_hours  int,                          -- 総勉強時間
    duration_weeks  int,                          -- 期間
    method_type     text CHECK (method_type IN ('exam_only', 'report_exam', 'schooling', 'media', 'other')),
    obtained_year   int,                          -- 取得年度
    outcome         text NOT NULL CHECK (outcome IN ('obtained', 'failed', 'in_progress')),

    -- 構造化されたサブセクション
    steps           jsonb DEFAULT '[]'::jsonb,    -- [{order, title, body, tips}, ...]
    tools_used      jsonb DEFAULT '[]'::jsonb,    -- [{type, name, note, link}, ...]
    pitfalls        jsonb DEFAULT '[]'::jsonb,    -- [{situation, solution}, ...]

    -- ソーシャルカウンタ（denormalized for performance）
    view_count      int DEFAULT 0,
    helpful_count   int DEFAULT 0,
    tsukurepo_count int DEFAULT 0,
    bookmark_count  int DEFAULT 0,

    -- AI 利用
    ai_used         boolean DEFAULT false,
    ai_usage_note   text,                         -- どこにどう AI を使ったか

    -- 検索
    search_vector   tsvector,
    embedding       vector(1536),                 -- Anthropic / OpenAI 埋め込み

    status          text NOT NULL DEFAULT 'published'
                    CHECK (status IN ('draft', 'published', 'hidden', 'flagged')),

    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),

    UNIQUE (author_id, subject_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_tani_recipes_subject_pub ON public.tani_recipes(subject_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tani_recipes_author ON public.tani_recipes(author_id);
CREATE INDEX IF NOT EXISTS idx_tani_recipes_search_pgroonga ON public.tani_recipes USING pgroonga (title, summary, body_md);
CREATE INDEX IF NOT EXISTS idx_tani_recipes_embedding ON public.tani_recipes USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_tani_recipes_helpful ON public.tani_recipes(helpful_count DESC) WHERE status = 'published';

-- ---------------------------------------------------------------------
-- つくれぽ（Reviews）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_reviews (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id           uuid NOT NULL REFERENCES public.tani_recipes(id) ON DELETE CASCADE,
    user_id             uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    outcome             text NOT NULL CHECK (outcome IN ('obtained', 'failed', 'in_progress')),
    obtained_year       int,
    difficulty_rating   smallint CHECK (difficulty_rating BETWEEN 1 AND 5),
    duration_actual     int,                       -- 実際にかかった時間
    body                text,
    photo_url           text,                      -- 任意（成績証明書スクショ等、ぼかし推奨）
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (recipe_id, user_id)                    -- 1レシピ1人1つくれぽ
);

CREATE INDEX IF NOT EXISTS idx_tani_reviews_recipe ON public.tani_reviews(recipe_id, created_at DESC);

-- ---------------------------------------------------------------------
-- リアクション（役に立った / やってみたい）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_reactions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    target_type     text NOT NULL CHECK (target_type IN ('recipe', 'review', 'comment')),
    target_id       uuid NOT NULL,
    type            text NOT NULL CHECK (type IN ('helpful', 'want_to_try')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, target_type, target_id, type)
);

CREATE INDEX IF NOT EXISTS idx_tani_reactions_target ON public.tani_reactions(target_type, target_id);

-- ---------------------------------------------------------------------
-- コメント
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_comments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id       uuid NOT NULL REFERENCES public.tani_recipes(id) ON DELETE CASCADE,
    user_id         uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    parent_id       uuid REFERENCES public.tani_comments(id) ON DELETE CASCADE,
    body            text NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tani_comments_recipe ON public.tani_comments(recipe_id, created_at);

-- ---------------------------------------------------------------------
-- ブックマーク
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_bookmarks (
    user_id         uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    recipe_id       uuid NOT NULL REFERENCES public.tani_recipes(id) ON DELETE CASCADE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, recipe_id)
);

-- ---------------------------------------------------------------------
-- レシピリクエスト（穴埋め誘導用）
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.tani_recipe_requests (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id      uuid NOT NULL REFERENCES public.tani_subjects(id) ON DELETE CASCADE,
    requester_id    uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    message         text,
    notified_when_filled boolean DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (subject_id, requester_id)
);

CREATE INDEX IF NOT EXISTS idx_tani_recipe_requests_subject ON public.tani_recipe_requests(subject_id);

-- ---------------------------------------------------------------------
-- カウンタの自動更新トリガー
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.tani_update_recipe_counters()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'tani_reactions' THEN
        IF TG_OP = 'INSERT' AND NEW.target_type = 'recipe' AND NEW.type = 'helpful' THEN
            UPDATE public.tani_recipes SET helpful_count = helpful_count + 1 WHERE id = NEW.target_id;
        ELSIF TG_OP = 'DELETE' AND OLD.target_type = 'recipe' AND OLD.type = 'helpful' THEN
            UPDATE public.tani_recipes SET helpful_count = GREATEST(helpful_count - 1, 0) WHERE id = OLD.target_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'tani_reviews' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE public.tani_recipes SET tsukurepo_count = tsukurepo_count + 1 WHERE id = NEW.recipe_id;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE public.tani_recipes SET tsukurepo_count = GREATEST(tsukurepo_count - 1, 0) WHERE id = OLD.recipe_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'tani_bookmarks' THEN
        IF TG_OP = 'INSERT' THEN
            UPDATE public.tani_recipes SET bookmark_count = bookmark_count + 1 WHERE id = NEW.recipe_id;
        ELSIF TG_OP = 'DELETE' THEN
            UPDATE public.tani_recipes SET bookmark_count = GREATEST(bookmark_count - 1, 0) WHERE id = OLD.recipe_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_tani_reactions_counter
    AFTER INSERT OR DELETE ON public.tani_reactions
    FOR EACH ROW EXECUTE FUNCTION public.tani_update_recipe_counters();

CREATE TRIGGER trg_tani_reviews_counter
    AFTER INSERT OR DELETE ON public.tani_reviews
    FOR EACH ROW EXECUTE FUNCTION public.tani_update_recipe_counters();

CREATE TRIGGER trg_tani_bookmarks_counter
    AFTER INSERT OR DELETE ON public.tani_bookmarks
    FOR EACH ROW EXECUTE FUNCTION public.tani_update_recipe_counters();

-- ---------------------------------------------------------------------
-- subjects.recipe_count の自動更新
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.tani_update_subject_counter()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.status = 'published' THEN
        UPDATE public.tani_subjects SET recipe_count = recipe_count + 1 WHERE id = NEW.subject_id;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.status != 'published' AND NEW.status = 'published' THEN
            UPDATE public.tani_subjects SET recipe_count = recipe_count + 1 WHERE id = NEW.subject_id;
        ELSIF OLD.status = 'published' AND NEW.status != 'published' THEN
            UPDATE public.tani_subjects SET recipe_count = GREATEST(recipe_count - 1, 0) WHERE id = NEW.subject_id;
        END IF;
    ELSIF TG_OP = 'DELETE' AND OLD.status = 'published' THEN
        UPDATE public.tani_subjects SET recipe_count = GREATEST(recipe_count - 1, 0) WHERE id = OLD.subject_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER trg_tani_recipes_subject_counter
    AFTER INSERT OR UPDATE OR DELETE ON public.tani_recipes
    FOR EACH ROW EXECUTE FUNCTION public.tani_update_subject_counter();

-- ---------------------------------------------------------------------
-- search_vector の自動更新
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.tani_recipes_update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.summary, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(NEW.body_md, '')), 'C');
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tani_recipes_search_vector
    BEFORE INSERT OR UPDATE ON public.tani_recipes
    FOR EACH ROW EXECUTE FUNCTION public.tani_recipes_update_search_vector();

-- ---------------------------------------------------------------------
-- Row Level Security (RLS)
-- ---------------------------------------------------------------------
ALTER TABLE public.tani_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_reactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tani_recipe_requests ENABLE ROW LEVEL SECURITY;

-- マスタは全員 read 可
CREATE POLICY "tani_universities_select" ON public.tani_universities FOR SELECT USING (true);
CREATE POLICY "tani_faculties_select" ON public.tani_faculties FOR SELECT USING (true);
CREATE POLICY "tani_subjects_select" ON public.tani_subjects FOR SELECT USING (true);

-- プロフィール
CREATE POLICY "tani_profiles_select_all" ON public.tani_profiles FOR SELECT USING (true);
CREATE POLICY "tani_profiles_insert_self" ON public.tani_profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "tani_profiles_update_self" ON public.tani_profiles FOR UPDATE USING (auth.uid() = id);

-- レシピ：published は全員、draft/hidden は本人のみ
CREATE POLICY "tani_recipes_select_published" ON public.tani_recipes FOR SELECT
    USING (status = 'published' OR auth.uid() = author_id);
CREATE POLICY "tani_recipes_insert_self" ON public.tani_recipes FOR INSERT WITH CHECK (auth.uid() = author_id);
CREATE POLICY "tani_recipes_update_self" ON public.tani_recipes FOR UPDATE USING (auth.uid() = author_id);
CREATE POLICY "tani_recipes_delete_self" ON public.tani_recipes FOR DELETE USING (auth.uid() = author_id);

-- つくれぽ
CREATE POLICY "tani_reviews_select_all" ON public.tani_reviews FOR SELECT USING (true);
CREATE POLICY "tani_reviews_insert_self" ON public.tani_reviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "tani_reviews_update_self" ON public.tani_reviews FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "tani_reviews_delete_self" ON public.tani_reviews FOR DELETE USING (auth.uid() = user_id);

-- リアクション
CREATE POLICY "tani_reactions_select_all" ON public.tani_reactions FOR SELECT USING (true);
CREATE POLICY "tani_reactions_insert_self" ON public.tani_reactions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "tani_reactions_delete_self" ON public.tani_reactions FOR DELETE USING (auth.uid() = user_id);

-- コメント
CREATE POLICY "tani_comments_select_all" ON public.tani_comments FOR SELECT USING (true);
CREATE POLICY "tani_comments_insert_self" ON public.tani_comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "tani_comments_update_self" ON public.tani_comments FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "tani_comments_delete_self" ON public.tani_comments FOR DELETE USING (auth.uid() = user_id);

-- ブックマーク（本人のみ可視）
CREATE POLICY "tani_bookmarks_select_self" ON public.tani_bookmarks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "tani_bookmarks_insert_self" ON public.tani_bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "tani_bookmarks_delete_self" ON public.tani_bookmarks FOR DELETE USING (auth.uid() = user_id);

-- リクエスト
CREATE POLICY "tani_requests_select_all" ON public.tani_recipe_requests FOR SELECT USING (true);
CREATE POLICY "tani_requests_insert_self" ON public.tani_recipe_requests FOR INSERT WITH CHECK (auth.uid() = requester_id);
CREATE POLICY "tani_requests_delete_self" ON public.tani_recipe_requests FOR DELETE USING (auth.uid() = requester_id);

-- =====================================================================
-- 注意事項
-- =====================================================================
-- 1. このマイグレーションは未適用。レビュー後に手動で適用すること。
-- 2. pgroonga が利用不可の場合、indexes は GIN + tsvector に置き換える。
-- 3. pgvector の dimension は使用する埋め込みモデルに合わせて調整。
--    Anthropic 経由なら voyage-3 (1024) など、要確認。
-- 4. 既存の Manabi スキーマ（profiles, listings 等）とは独立して動作する。
--    `tani_` プレフィックスで衝突を回避済み。
