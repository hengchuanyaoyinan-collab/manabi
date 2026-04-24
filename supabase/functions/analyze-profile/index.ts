import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "jsr:@supabase/supabase-js@2";

const ALLOWED_ORIGINS = [
  "https://manabi-bay.vercel.app",
];

function getCors(req: Request) {
  const origin = req.headers.get("origin") ?? "";
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: getCors(req) });
  }
  if (req.method !== "POST") {
    return new Response("method_not_allowed", { status: 405 });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) throw new Error("Missing auth");

    const supabase = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    const token = authHeader.replace("Bearer ", "");
    const { data: { user }, error: authErr } = await createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!
    ).auth.getUser(token);
    if (authErr || !user) throw new Error("Unauthorized");

    const body = await req.json().catch(() => ({}));
    const targetUserId = body.user_id || user.id;

    const [profileRes, skillsRes, reviewsRes] = await Promise.all([
      supabase.from("profiles").select("*").eq("id", targetUserId).single(),
      supabase.from("skills").select("*").eq("user_id", targetUserId),
      supabase.from("reviews").select("rating, comment").eq("reviewee_id", targetUserId).limit(20),
    ]);

    const profile = profileRes.data;
    const skills = skillsRes.data || [];
    const reviews = reviewsRes.data || [];

    if (!profile) throw new Error("Profile not found");
    if (skills.length === 0) throw new Error("No skills registered");

    const profileText = [
      `名前: ${profile.name || "未設定"}`,
      `自己紹介: ${profile.bio || "なし"}`,
      `経歴: ${profile.career || "なし"}`,
      `実績: ${profile.achievements || "なし"}`,
      `指導スタイル: ${profile.teaching_style || "未設定"}`,
      `信頼スコア: ${profile.score || 0}`,
      `\nスキル一覧:`,
      ...skills.map((s: any, i: number) =>
        `  ${i + 1}. ${s.subject} - ${s.description || "説明なし"} / 料金: ¥${s.price_min || 0}~ / エリア: ${s.area || "未設定"} / 曜日: ${(s.available_days || []).join(",")} / 形式: ${(s.lesson_formats || []).join(",")} / タグ: ${(s.tags || []).join(",")}`
      ),
      reviews.length > 0 ? `\nレビュー (${reviews.length}件): ${reviews.map((r: any) => `★${r.rating} ${r.comment || ""}`).join(" | ")}` : "",
    ].filter(Boolean).join("\n");

    const OPENAI_KEY = Deno.env.get("OPENAI_API_KEY");
    if (!OPENAI_KEY) throw new Error("OPENAI_API_KEY not configured");

    const analysisRes = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${OPENAI_KEY}` },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        temperature: 0.3,
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content: `あなたはスキルシェアプラットフォームのAIプロフィール分析官です。
教師のプロフィール情報を分析し、以下のJSON形式で出力してください:
{
  "skills_summary": "この先生の強みと特徴を2-3文で要約（日本語）",
  "teaching_strengths": ["強み1", "強み2", "強み3"],
  "experience_level": "beginner|intermediate|advanced|expert",
  "personality_tags": ["親切", "丁寧" など性格タグ 3-5個],
  "subject_keywords": ["英会話", "TOEIC" など検索用キーワード 5-10個],
  "ideal_student": "どんな生徒に最適か（日本語1文）",
  "matching_signals": ["この先生にマッチする生徒のリクエスト特徴 3-5個"]
}`
          },
          { role: "user", content: profileText }
        ]
      })
    });

    if (!analysisRes.ok) {
      const err = await analysisRes.text();
      throw new Error(`OpenAI analysis failed: ${err}`);
    }

    const analysisData = await analysisRes.json();
    const analysis = JSON.parse(analysisData.choices[0].message.content);

    const embeddingText = [
      analysis.skills_summary,
      `強み: ${analysis.teaching_strengths?.join(", ")}`,
      `キーワード: ${analysis.subject_keywords?.join(", ")}`,
      `理想の生徒: ${analysis.ideal_student}`,
      `マッチシグナル: ${analysis.matching_signals?.join(", ")}`,
      profileText,
    ].join("\n");

    const embRes = await fetch("https://api.openai.com/v1/embeddings", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${OPENAI_KEY}` },
      body: JSON.stringify({ model: "text-embedding-3-small", input: embeddingText })
    });

    if (!embRes.ok) {
      const err = await embRes.text();
      throw new Error(`OpenAI embedding failed: ${err}`);
    }

    const embData = await embRes.json();
    const embedding = embData.data[0].embedding;

    const { error: upsertErr } = await supabase
      .from("ai_profiles")
      .upsert({
        user_id: targetUserId,
        embedding,
        skills_summary: analysis.skills_summary,
        teaching_strengths: analysis.teaching_strengths || [],
        experience_level: analysis.experience_level || "intermediate",
        personality_tags: analysis.personality_tags || [],
        subject_keywords: analysis.subject_keywords || [],
        analyzed_at: new Date().toISOString(),
        raw_analysis: analysis,
      }, { onConflict: "user_id" });

    if (upsertErr) throw new Error(`DB upsert failed: ${upsertErr.message}`);

    return new Response(
      JSON.stringify({
        success: true,
        analysis: {
          skills_summary: analysis.skills_summary,
          teaching_strengths: analysis.teaching_strengths,
          experience_level: analysis.experience_level,
          personality_tags: analysis.personality_tags,
        }
      }),
      { headers: { ...getCors(req), "Content-Type": "application/json" } }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 400, headers: { ...getCors(req), "Content-Type": "application/json" } }
    );
  }
});
