// Autocomplete över yrkestitlar MED publicerbar statistik (n≥5). Driver
// sökfältet i beställnings-UI:t. Returnerar {slug,title} (max 10).
import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request): Promise<Response> {
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") ?? "").trim();
  if (q.length < 2) return NextResponse.json({ results: [] });

  // ilike-sök på titel; !inner mot national-stats säkrar n≥5.
  const { data, error } = await supabaseAdmin
    .from("generalized_titles")
    .select("slug, title, title_national_stats!inner(n)")
    .ilike("title", `%${q}%`)
    .order("title", { ascending: true })
    .limit(10);

  if (error) return NextResponse.json({ results: [] }, { status: 500 });

  const results = (data ?? []).map((r: any) => ({ slug: r.slug, title: r.title }));
  return NextResponse.json({ results });
}
