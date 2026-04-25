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
  const cors = getCors(req);
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: cors });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method_not_allowed" }), {
      status: 405,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  try {
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) throw new Error("Missing auth");

    const token = authHeader.replace("Bearer ", "");
    const anonClient = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_ANON_KEY")!
    );
    const { data: { user }, error: authErr } = await anonClient.auth.getUser(token);
    if (authErr || !user) throw new Error("Unauthorized");

    const body = await req.json().catch(() => ({}));
    const { prompt } = body;
    if (!prompt || typeof prompt !== "string" || prompt.length < 10) {
      return new Response(JSON.stringify({ error: "invalid_prompt" }), {
        status: 400,
        headers: { ...cors, "Content-Type": "application/json" },
      });
    }

    const OPENAI_KEY = Deno.env.get("OPENAI_API_KEY");
    if (!OPENAI_KEY) throw new Error("OPENAI_API_KEY not configured");

    const ac = new AbortController();
    const timeout = setTimeout(() => ac.abort(), 30000);
    const res = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_KEY}`,
      },
      signal: ac.signal,
      body: JSON.stringify({
        model: "gpt-4o-mini",
        temperature: 0.7,
        max_tokens: 500,
        messages: [
          {
            role: "system",
            content: `You are a professional copywriter for a Japanese skill-sharing platform called Manabi.
Generate a warm, professional self-introduction bio in Japanese.
The bio should:
- Be 200-350 characters
- Sound natural and inviting
- Highlight the teacher's strengths
- Make students want to learn from this teacher
- Use polite but approachable Japanese
- NOT use emojis
- Have 2-3 short paragraphs
Output ONLY the bio text, nothing else.`,
          },
          { role: "user", content: prompt },
        ],
      }),
    });

    clearTimeout(timeout);
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`OpenAI failed: ${err}`);
    }

    const data = await res.json();
    const bio = data.choices?.[0]?.message?.content?.trim() || "";

    return new Response(JSON.stringify({ bio }), {
      headers: { ...cors, "Content-Type": "application/json" },
    });
  } catch (err: any) {
    console.error("generate-bio error:", err.message);
    return new Response(JSON.stringify({ error: err.message }), {
      status: 400,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }
});
