#!/usr/bin/env python3
"""Genererar granskningslista inför go-live (steg 1 i go-live-sekvensen).

Kör automatiska DB-kontroller av granskningsändringarna och skriver en
stratifierad stickprovslista (markdown) med exit-kriterium för den sista
manuella ögningen av preview-deployen.

Användning (från repo-roten, med molnets DATABASE_URL, t.ex. session-poolern):

    DATABASE_URL="postgresql://...@aws-0-eu-north-1.pooler.supabase.com:5432/postgres" \
        python pipeline/granskningslista.py --base http://localhost:3000 \
        --out granskningslista.md

--base: adress att bygga sidlänkar mot. Använd `next start` lokalt
(http://localhost:3000) eller preview-URL:en om du är SSO-inloggad i webbläsaren.

Skriptet introspekterar kolumnnamn (pg_attribute) och hoppar över strata det
inte kan lösa, med notering i utdatan – ingenting kraschar på ett kolumnnamn.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys

try:
    import psycopg2
except ImportError:
    sys.exit("psycopg2 saknas: pip install psycopg2-binary")

# Kandidat-kolumnnamn (introspekteras mot faktiskt schema)
CAND_N = ["n", "antal", "count", "employee_count", "num_records", "record_count", "cnt"]
CAND_SLUG = ["slug", "title_slug", "generalized_title_slug"]
CAND_ID = ["generalized_title_id", "title_id", "gt_id"]
CAND_TITLE = ["title", "name", "generalized_title", "display_name"]

NATIONAL = "title_national_stats"
EMPLOYER_ALL = "title_employer_all"
GT = "generalized_titles"


def relation_columns(cur, relname: str) -> list[str]:
    """Kolumner för tabell ELLER materialiserad vy (information_schema saknar matviews)."""
    cur.execute(
        """
        SELECT a.attname
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace ns ON ns.oid = c.relnamespace
        WHERE c.relname = %s AND ns.nspname = 'public'
          AND a.attnum > 0 AND NOT a.attisdropped
        """,
        (relname,),
    )
    return [r[0] for r in cur.fetchall()]


def pick(columns: list[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in columns:
            return c
    return None


class Ctx:
    """Löst schema: joinvillkor gt <-> matviews m.m."""

    def __init__(self, cur):
        self.notes: list[str] = []
        self.gt_cols = relation_columns(cur, GT)
        self.nat_cols = relation_columns(cur, NATIONAL)
        self.emp_cols = relation_columns(cur, EMPLOYER_ALL)

        self.gt_title = pick(self.gt_cols, CAND_TITLE) or "slug"
        self.nat_n = pick(self.nat_cols, CAND_N)
        self.emp_n = pick(self.emp_cols, CAND_N)

        self.nat_join = self._join("s", self.nat_cols)
        self.emp_join = self._join("s", self.emp_cols)

        if not self.nat_cols:
            self.notes.append(f"Hittade inte {NATIONAL} – flera strata överhoppade.")
        if not self.emp_cols:
            self.notes.append(f"Hittade inte {EMPLOYER_ALL} – n<5-stratum överhoppat.")

    def _join(self, alias: str, cols: list[str]) -> str | None:
        slug = pick(cols, CAND_SLUG)
        if slug:
            return f"{alias}.{slug} = gt.slug"
        idc = pick(cols, CAND_ID)
        if idc and "id" in self.gt_cols:
            return f"{alias}.{idc} = gt.id"
        return None


def fetch(cur, sql: str, params=()) -> list[tuple]:
    cur.execute(sql, params)
    return cur.fetchall()


def try_fetch(cur, ctx: Ctx, label: str, sql: str, params=()) -> list[tuple]:
    try:
        return fetch(cur, sql, params)
    except Exception as e:  # noqa: BLE001 – rapportera och gå vidare
        cur.connection.rollback()
        ctx.notes.append(f"Stratum/kontroll '{label}' överhoppad: {e}".splitlines()[0])
        return []


# ---------------------------------------------------------------- automatiska kontroller

def auto_checks(cur, ctx: Ctx) -> list[str]:
    out = []

    def check(label: str, sql: str, expect_zero=True, fmt="{v}"):
        try:
            v = fetch(cur, sql)[0][0]
        except Exception as e:  # noqa: BLE001
            cur.connection.rollback()
            out.append(f"- [ ] {label}: KUNDE INTE KÖRAS ({str(e).splitlines()[0]})")
            return
        ok = (v == 0) if expect_zero else (v > 0)
        mark = "x" if ok else " "
        warn = "" if ok else "  **<-- AVVIKELSE, utred före go-live**"
        out.append(f"- [{mark}] {label}: {fmt.format(v=v)}{warn}")

    check(
        "ai_description fri från HTML-taggar (förväntat 0)",
        f"SELECT count(*) FROM {GT} WHERE ai_description ~ '<[a-zA-Z/]'",
    )
    check(
        "received_at satt på alla källdokument (förväntat 0 NULL)",
        "SELECT count(*) FROM source_documents WHERE received_at IS NULL",
    )
    if ctx.nat_n:
        check(
            "publika nationella vyn innehåller inga n<5 (förväntat 0)",
            f"SELECT count(*) FROM {NATIONAL} WHERE {ctx.nat_n} < 5",
        )
    check(
        "kön i salary_records endast K/M/NULL (förväntat 0 övriga)",
        "SELECT count(*) FROM salary_records"
        " WHERE gender IS NOT NULL AND gender NOT IN ('K','M')",
    )
    check(
        "tim/månad aldrig blandat (förväntat 0)",
        "SELECT count(*) FROM salary_records"
        " WHERE hourly_salary IS NOT NULL AND monthly_salary IS NOT NULL",
    )
    return out


# ---------------------------------------------------------------- strata

def strata(cur, ctx: Ctx, k: int) -> list[tuple[str, str, list[tuple[str, str]]]]:
    """[(rubrik, instruktion, [(titel, slug), ...]), ...]"""
    res = []
    t = ctx.gt_title

    if ctx.nat_join and ctx.nat_n:
        res.append((
            "Störst underlag (layout under tryck, många arbetsgivarrader)",
            "Kontrollera tabellrendering, utfällbar källista, laddtid.",
            try_fetch(cur, ctx, "störst underlag",
                f"SELECT gt.{t}, gt.slug FROM {GT} gt JOIN {NATIONAL} s ON {ctx.nat_join}"
                f" ORDER BY s.{ctx.nat_n} DESC LIMIT %s", (k,)),
        ))
        res.append((
            "Slumpade titlar med publicerbar data",
            "Normalfallet: statistik rimlig, styckeindelad beskrivning, källhänvisning + datum.",
            try_fetch(cur, ctx, "slumpade med data",
                f"SELECT gt.{t}, gt.slug FROM {GT} gt JOIN {NATIONAL} s ON {ctx.nat_join}"
                f" ORDER BY random() LIMIT %s", (k,)),
        ))
        res.append((
            "Informationssidor utan publicerbar data",
            "Kategoristatistik, similar_jobs-länkar, förklaringstext – inga tomma tabeller.",
            try_fetch(cur, ctx, "info-sidor",
                f"SELECT gt.{t}, gt.slug FROM {GT} gt"
                f" WHERE NOT EXISTS (SELECT 1 FROM {NATIONAL} s WHERE {ctx.nat_join})"
                f" ORDER BY random() LIMIT %s", (k,)),
        ))

    if ctx.emp_join and ctx.emp_n:
        res.append((
            "Titlar med n<5-arbetsgivarrader",
            "Raden ska visa antal MEN INGA lönevärden (granskningsändring 5).",
            try_fetch(cur, ctx, "n<5-rader",
                f"SELECT * FROM (SELECT DISTINCT gt.{t}, gt.slug FROM {GT} gt"
                f" JOIN {EMPLOYER_ALL} s ON {ctx.emp_join}"
                f" WHERE s.{ctx.emp_n} < 5) q ORDER BY random() LIMIT %s", (k,)),
        ))

    res.append((
        "Längst ai_description (städningen syns tydligast här)",
        "Flera stycken, ingen '<p>' eller annan råtagg, meta-description ren text (view-source).",
        try_fetch(cur, ctx, "längst beskrivning",
            f"SELECT {t}, slug FROM {GT} WHERE ai_description IS NOT NULL"
            f" ORDER BY length(ai_description) DESC LIMIT 3"),
    ))
    res.append((
        "Nyligen flyttade kategorier (session 5/6-flyttar)",
        "Titeln ska ligga i rimlig kategori; brödsmula/kategorilänk stämmer.",
        try_fetch(cur, ctx, "flyttade kategorier",
            f"SELECT {t}, slug FROM {GT} WHERE category_reviewed = false"
            f" ORDER BY random() LIMIT 8"),
    ))
    return res


# ---------------------------------------------------------------- markdown

def render(base: str, checks: list[str],
           groups: list[tuple[str, str, list[tuple[str, str]]]],
           redirect_slugs: list[str], notes: list[str]) -> str:
    today = dt.date.today().isoformat()
    L: list[str] = []
    L.append(f"# Granskningslista – preview före go-live ({today})")
    L.append("")
    L.append(f"Sidbas: `{base}`")
    L.append("")
    L.append("## Exit-kriterium")
    L.append("")
    L.append("Granskningen är **KLAR** – och steg 2 (promote) får köras – när alla rutor")
    L.append("nedan är ibockade och inga fynd kräver data- eller kodändring. Fynd som kräver")
    L.append("ändring: åtgärda, deploya ny preview, kör om detta skript, börja om på listan.")
    L.append("Ingen tredje kategori (\"tar det sen\") – då blir det aldrig go-live.")
    L.append("")
    L.append("## A. Automatiska kontroller (kördes av skriptet)")
    L.append("")
    L.extend(checks)
    L.append("")
    L.append("## B. Sidor att ögna")
    L.append("")
    L.append("Per sida: rubrik/titel korrekt, statistik rimlig, källhänvisning med")
    L.append("utlämningsdatum, datering \"2024 års insamling / augusti 2026\", styckeindelad")
    L.append("beskrivning utan råa taggar, **ingen 2026-uppräkning synlig** (flaggan är AV).")
    L.append("")
    for heading, instruction, rows in groups:
        L.append(f"### {heading}")
        L.append("")
        L.append(f"_{instruction}_")
        L.append("")
        if not rows:
            L.append("_(inga rader – stratum tomt eller överhoppat, se noteringar)_")
        for title, slug in rows:
            L.append(f"- [ ] {title} — {base}/yrken/{slug}")
        L.append("")
    L.append("## C. Fasta kontroller (en gång, valfri sida om inget annat anges)")
    L.append("")
    L.append("- [ ] Footer: databasens namn \"Offentliga löner, offentligaloner.se\",")
    L.append("      tillhandahållare, ansvarig utgivare Patrik Larsson, utgivningsbevis")
    L.append("      nr 2024-077 – syns på varje sida.")
    L.append("- [ ] Källhänvisning: aggregerad rad + utfällbar lista fungerar (matview 0006).")
    L.append("- [ ] Startsida + en kategorisida renderar och länkar rätt.")
    L.append("- [ ] Mobilbredd: yrkessida med bred tabell är läsbar.")
    L.append("")
    L.append("## D. Redirects (förväntat: 301 + Location mot /yrken/...)")
    L.append("")
    L.append("```bash")
    for slug in redirect_slugs:
        L.append(f"curl -sI {base}/loner/{slug} | grep -Ei 'HTTP|location'")
    L.append("# plus minst en retirerad numrerad oktober-slug ur next.config:")
    L.append(f"# curl -sI {base}/loner/<numrerad-slug> | grep -Ei 'HTTP|location'")
    L.append("```")
    L.append("")
    if notes:
        L.append("## Noteringar från skriptet")
        L.append("")
        L.extend(f"- {n}" for n in notes)
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://localhost:3000",
                    help="Bas-URL för sidlänkar (default http://localhost:3000)")
    ap.add_argument("--out", default="granskningslista.md", help="Utfil (markdown)")
    ap.add_argument("-k", type=int, default=5, help="Antal sidor per stratum (default 5)")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Sätt DATABASE_URL (molnets session-pooler).")

    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    ctx = Ctx(cur)

    checks = auto_checks(cur, ctx)
    groups = strata(cur, ctx, args.k)

    redirect_rows = try_fetch(cur, ctx, "redirect-sample",
        f"SELECT slug FROM {GT} ORDER BY random() LIMIT 3")
    redirect_slugs = [r[0] for r in redirect_rows]

    md = render(args.base.rstrip("/"), checks, groups, redirect_slugs, ctx.notes)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)

    failures = [c for c in checks if c.startswith("- [ ]")]
    print(f"Skrev {args.out}.")
    print(f"Automatiska kontroller: {len(checks) - len(failures)}/{len(checks)} gröna.")
    if failures:
        print("AVVIKELSER:")
        for f_ in failures:
            print("  " + f_)
        sys.exit(1)


if __name__ == "__main__":
    main()
