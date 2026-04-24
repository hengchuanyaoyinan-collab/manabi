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

const WEIGHTS = {
  embedding_similarity: 0.35,
  subject_match: 0.20,
  availability_match: 0.15,
  price_fit: 0.10,
  rating_score: 0.10,
  profile_completeness: 0.05,
  feedback_boost: 0.05,
};

Deno.serve(async (req: Request) => {
  const cors = getCors(req);

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors });
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

    const body = await req.json();
    const { action } = body;

    if (action === "create_and_match") {
      return await createAndMatch(supabase, user.id, body, cors);
    } else if (action === "rematch") {
      return await rematch(supabase, user.id, body.request_id, cors);
    } else if (action === "feedback") {
      return await recordFeedback(supabase, user.id, body, cors);
    } else {
      throw new Error("Invalid action. Use: create_and_match, rematch, feedback");
    }
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 400, headers: { ...cors, "Content-Type": "application/json" } }
    );
  }
});

async function createAndMatch(supabase: any, userId: string, body: any, cors: Record<string, string>) {
  const { subject, detail, budget, format } = body;
  if (!subject) throw new Error("subject is required");

  const OPENAI_KEY = Deno.env.get("OPENAI_API_KEY");
  if (!OPENAI_KEY) throw new Error("OPENAI_API_KEY not configured");

  const structureRes = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${OPENAI_KEY}` },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      temperature: 0.2,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `スキルシェアプラットフォームのリクエスト構造化AIです。
ユーザーの学びたいリクエストを分析し、JSONで出力してください:
{
  "parsed_subject": "正規化された科目名",
  "skill_level": "beginner|intermediate|advanced",
  "goals": ["学習目標 2-3個"],
  "preferred_style": "friendly|structured|practical|patient|intensive",
  "preferred_format": "online|inperson|any",
  "time_preference": "希望時間帯の推定",
  "budget_range": { "min": 0, "max": 0 },
  "urgency": "low|normal|high|urgent",
  "keywords": ["検索用キーワード 5-8個"],
  "ideal_teacher_traits": ["理想の先生の特徴 3-5個"]
}`
        },
        {
          role: "user",
          content: `科目: ${subject}\n詳細: ${detail || "なし"}\n予算: ${budget ? `¥${budget}` : "未指定"}\n形式: ${format || "any"}`
        }
      ]
    })
  });

  if (!structureRes.ok) throw new Error("AI structuring failed");
  const structureData = await structureRes.json();
  const structured = JSON.parse(structureData.choices[0].message.content);

  const requestText = [
    `学びたいこと: ${subject} ${detail || ""}`,
    `レベル: ${structured.skill_level}`,
    `目標: ${structured.goals?.join(", ")}`,
    `希望スタイル: ${structured.preferred_style}`,
    `理想の先生: ${structured.ideal_teacher_traits?.join(", ")}`,
    `キーワード: ${structured.keywords?.join(", ")}`,
  ].join("\n");

  const embRes = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${OPENAI_KEY}` },
    body: JSON.stringify({ model: "text-embedding-3-small", input: requestText })
  });

  if (!embRes.ok) throw new Error("Embedding generation failed");
  const embData = await embRes.json();
  const requestEmbedding = embData.data[0].embedding;

  const { data: request, error: reqErr } = await supabase
    .from("learning_requests")
    .insert({
      user_id: userId,
      subject: structured.parsed_subject || subject,
      detail: detail || "",
      budget: budget || null,
      format: structured.preferred_format || format || "any",
      status: "open",
      embedding: requestEmbedding,
      ai_structured: structured,
      preferred_style: structured.preferred_style,
      skill_level: structured.skill_level,
      urgency: structured.urgency || "normal",
    })
    .select()
    .single();

  if (reqErr) throw new Error(`Request save failed: ${reqErr.message}`);

  const matches = await findAndScoreMatches(
    supabase, OPENAI_KEY, request, requestEmbedding, structured, userId
  );

  return new Response(
    JSON.stringify({ success: true, request_id: request.id, matches, structured }),
    { headers: { ...cors, "Content-Type": "application/json" } }
  );
}

async function rematch(supabase: any, userId: string, requestId: string, cors: Record<string, string>) {
  if (!requestId) throw new Error("request_id is required");

  const OPENAI_KEY = Deno.env.get("OPENAI_API_KEY");
  if (!OPENAI_KEY) throw new Error("OPENAI_API_KEY not configured");

  const { data: request, error } = await supabase
    .from("learning_requests")
    .select("*")
    .eq("id", requestId)
    .eq("user_id", userId)
    .single();

  if (error || !request) throw new Error("Request not found");

  const matches = await findAndScoreMatches(
    supabase, OPENAI_KEY, request, request.embedding,
    request.ai_structured || {}, userId
  );

  return new Response(
    JSON.stringify({ success: true, request_id: requestId, matches }),
    { headers: { ...cors, "Content-Type": "application/json" } }
  );
}

async function recordFeedback(supabase: any, userId: string, body: any, cors: Record<string, string>) {
  const { match_id, feedback_action, rating, metadata } = body;
  if (!match_id || !feedback_action) throw new Error("match_id and feedback_action required");

  const { error } = await supabase.from("match_feedback").insert({
    match_id,
    user_id: userId,
    action: feedback_action,
    rating: rating || null,
    metadata: metadata || {},
  });

  if (error) throw new Error(`Feedback save failed: ${error.message}`);

  if (feedback_action === "accepted" || feedback_action === "book") {
    await supabase.from("ai_matches")
      .update({ status: "accepted", updated_at: new Date().toISOString() })
      .eq("id", match_id);
  } else if (feedback_action === "dismiss" || feedback_action === "skip") {
    await supabase.from("ai_matches")
      .update({ status: "declined", updated_at: new Date().toISOString() })
      .eq("id", match_id);
  }

  return new Response(
    JSON.stringify({ success: true }),
    { headers: { ...cors, "Content-Type": "application/json" } }
  );
}

async function findAndScoreMatches(
  supabase: any,
  openaiKey: string,
  request: any,
  requestEmbedding: number[],
  structured: any,
  userId: string
) {
  const { data: vectorMatches } = await supabase
    .rpc("match_teachers", {
      query_embedding: requestEmbedding,
      match_threshold: 0.15,
      match_count: 30,
    });

  const candidateIds = (vectorMatches || []).map((m: any) => m.user_id);
  const similarityMap = new Map(
    (vectorMatches || []).map((m: any) => [m.user_id, m.similarity])
  );

  const sanitizedSubject = (request.subject || "").replace(/[%_,(){}."'\\]/g, "");
  const { data: keywordSkills } = await supabase
    .from("skills")
    .select("user_id, subject, price_min, available_days, lesson_formats, area, tags, description, id")
    .or(`subject.ilike.%${sanitizedSubject}%,tags.cs.{${sanitizedSubject}}`);

  const keywordTeacherIds = (keywordSkills || [])
    .map((s: any) => s.user_id)
    .filter((id: string) => id !== userId);

  const allCandidateIds = [...new Set([...candidateIds, ...keywordTeacherIds])]
    .filter(id => id !== userId);

  if (allCandidateIds.length === 0) return [];

  const [profilesRes, skillsRes, aiProfilesRes, feedbackRes] = await Promise.all([
    supabase.from("profiles").select("*").in("id", allCandidateIds),
    supabase.from("skills").select("*").in("user_id", allCandidateIds),
    supabase.from("ai_profiles").select("*").in("user_id", allCandidateIds),
    supabase.from("match_feedback").select("match_id, action").eq("user_id", userId),
  ]);

  const profiles = profilesRes.data || [];
  const allSkills = skillsRes.data || [];
  const aiProfiles = aiProfilesRes.data || [];

  const profileMap = new Map(profiles.map((p: any) => [p.id, p]));
  const skillsByUser = new Map<string, any[]>();
  for (const s of allSkills) {
    if (!skillsByUser.has(s.user_id)) skillsByUser.set(s.user_id, []);
    skillsByUser.get(s.user_id)!.push(s);
  }
  const aiProfileMap = new Map(aiProfiles.map((a: any) => [a.user_id, a]));

  const scored: any[] = [];
  const budgetMax = structured.budget_range?.max || request.budget || 99999;
  const budgetMin = structured.budget_range?.min || 0;

  for (const teacherId of allCandidateIds) {
    const profile = profileMap.get(teacherId);
    if (!profile) continue;

    const teacherSkills = skillsByUser.get(teacherId) || [];
    const aiProfile = aiProfileMap.get(teacherId);
    const sim = similarityMap.get(teacherId) || 0;

    let bestSkill: any = null;
    let bestSubjectScore = 0;
    for (const skill of teacherSkills) {
      let subScore = 0;
      const subjectLower = (skill.subject || "").toLowerCase();
      const reqSubjectLower = (request.subject || "").toLowerCase();
      if (subjectLower === reqSubjectLower) subScore = 1.0;
      else if (subjectLower.includes(reqSubjectLower) || reqSubjectLower.includes(subjectLower)) subScore = 0.7;
      else if ((skill.tags || []).some((t: string) => t.toLowerCase().includes(reqSubjectLower))) subScore = 0.5;

      if (subScore > bestSubjectScore) {
        bestSubjectScore = subScore;
        bestSkill = skill;
      }
    }
    if (!bestSkill && teacherSkills.length > 0) bestSkill = teacherSkills[0];

    const embeddingScore = Math.min(sim / 0.7, 1.0);
    const subjectScore = bestSubjectScore;

    const teacherDays = new Set(bestSkill?.available_days || []);
    let availScore = teacherDays.size > 0 ? 0.5 : 0;

    const price = bestSkill?.price_min || 0;
    let priceScore = 0.5;
    if (price > 0 && budgetMax < 99999) {
      if (price <= budgetMax && price >= budgetMin) priceScore = 1.0;
      else if (price <= budgetMax * 1.2) priceScore = 0.6;
      else if (price <= budgetMax * 1.5) priceScore = 0.3;
      else priceScore = 0.1;
    }

    const ratingScore = Math.min((profile.score || 0) / 80, 1.0);

    let completeness = 0;
    if (profile.bio) completeness += 0.25;
    if (profile.career) completeness += 0.25;
    if (profile.teaching_style) completeness += 0.25;
    if (aiProfile) completeness += 0.25;

    const feedbackBoost = 0.5;

    const totalScore = (
      embeddingScore * WEIGHTS.embedding_similarity +
      subjectScore * WEIGHTS.subject_match +
      availScore * WEIGHTS.availability_match +
      priceScore * WEIGHTS.price_fit +
      ratingScore * WEIGHTS.rating_score +
      completeness * WEIGHTS.profile_completeness +
      feedbackBoost * WEIGHTS.feedback_boost
    ) * 100;

    scored.push({
      teacher_id: teacherId,
      skill_id: bestSkill?.id,
      profile,
      skill: bestSkill,
      aiProfile,
      score: Math.round(totalScore * 100) / 100,
      breakdown: {
        embedding: Math.round(embeddingScore * 100),
        subject: Math.round(subjectScore * 100),
        availability: Math.round(availScore * 100),
        price: Math.round(priceScore * 100),
        rating: Math.round(ratingScore * 100),
        completeness: Math.round(completeness * 100),
      },
    });
  }

  scored.sort((a, b) => b.score - a.score);
  const topMatches = scored.slice(0, 10);
  if (topMatches.length === 0) return [];

  const reasonsPrompt = topMatches.map((m, i) => {
    const s = m.skill;
    const p = m.profile;
    return `${i + 1}. ${p.name} (スコア:${m.score}) - ${s?.subject || "未設定"}, ¥${s?.price_min || 0}~, 強み: ${m.aiProfile?.teaching_strengths?.join(",") || p.teaching_style || "不明"}`;
  }).join("\n");

  const reasonsRes = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${openaiKey}` },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      temperature: 0.5,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `スキルシェアプラットフォームのAIマッチングアドバイザーです。
各先生がなぜこの生徒に合うか、短く親しみやすい日本語で推薦理由を生成してください。
各推薦理由は40-60文字程度。具体的なポイントを挙げる。
出力: { "reasons": ["理由1", "理由2", ...] } ← 先生の順番と同じ`
        },
        {
          role: "user",
          content: `生徒のリクエスト: ${request.subject} - ${request.detail || "詳細なし"}
レベル: ${structured.skill_level || "未指定"}
目標: ${structured.goals?.join(", ") || "未指定"}

候補の先生:
${reasonsPrompt}`
        }
      ]
    })
  });

  let reasons: string[] = [];
  if (reasonsRes.ok) {
    const reasonsData = await reasonsRes.json();
    const parsed = JSON.parse(reasonsData.choices[0].message.content);
    reasons = parsed.reasons || [];
  }

  const matchRows = topMatches.map((m, i) => ({
    request_id: request.id,
    teacher_id: m.teacher_id,
    skill_id: m.skill_id,
    score: m.score,
    score_breakdown: m.breakdown,
    ai_reason: reasons[i] || `${m.profile.name}さんは${m.skill?.subject || "この分野"}の経験豊富な先生です`,
    status: "recommended",
  }));

  const { data: savedMatches, error: matchErr } = await supabase
    .from("ai_matches")
    .upsert(matchRows, { onConflict: "request_id,teacher_id" })
    .select();

  if (matchErr) console.error("Match save error:", matchErr);

  return topMatches.map((m, i) => ({
    match_id: savedMatches?.[i]?.id || null,
    teacher: {
      id: m.teacher_id,
      name: m.profile.name,
      avatar_url: m.profile.avatar_url,
      bio: m.profile.bio,
      score: m.profile.score,
      teaching_style: m.profile.teaching_style,
    },
    skill: m.skill ? {
      id: m.skill.id,
      subject: m.skill.subject,
      price_min: m.skill.price_min,
      area: m.skill.area,
      available_days: m.skill.available_days,
      lesson_formats: m.skill.lesson_formats,
      description: m.skill.description,
      tags: m.skill.tags,
    } : null,
    match_score: m.score,
    score_breakdown: m.breakdown,
    ai_reason: reasons[i] || matchRows[i].ai_reason,
    ai_profile: m.aiProfile ? {
      strengths: m.aiProfile.teaching_strengths,
      personality: m.aiProfile.personality_tags,
      experience: m.aiProfile.experience_level,
    } : null,
  }));
}
