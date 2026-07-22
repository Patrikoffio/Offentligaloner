#!/usr/bin/env python3
"""
Städa generalized_titles.ai_description: ta bort HTML-taggar och normalisera till
ren text med tomrad (\\n\\n) mellan stycken. Styckesgräns härleds ur </p><p>.

Beskrivningarna är migrerat, bevarat innehåll – vi ändrar bara presentationen
(taggar → styckesindelad ren text), inte texten i sig.

Dry-run som standard; --apply utför UPDATE. Ange --db-url (eller DATABASE_URL).
"""

import argparse
import os
import re
import sys

import psycopg2

# </p> ... <p> (ev. whitespace/attribut) → styckesgräns
_PARA_BREAK = re.compile(r"</p\s*>\s*<p[^>]*>", re.IGNORECASE)
_ANY_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")
_MULTINL = re.compile(r"\n{3,}")


def clean(html: str | None) -> str | None:
    if html is None:
        return None
    t = _PARA_BREAK.sub("\n\n", html)     # inre styckesgränser → tomrad
    t = _ANY_TAG.sub("", t)                # ta bort kvarvarande taggar (<p>, </p>, ev. andra)
    # normalisera varje stycke: kollapsa whitespace, trimma
    paras = [ _WS.sub(" ", p).strip() for p in re.split(r"\n\s*\n", t) ]
    paras = [ p for p in paras if p ]
    return "\n\n".join(paras) if paras else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres"))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    conn = psycopg2.connect(args.db_url)
    cur = conn.cursor()
    cur.execute("SELECT id, ai_description FROM generalized_titles WHERE ai_description IS NOT NULL")
    rows = cur.fetchall()

    updates = []
    changed = 0
    for tid, desc in rows:
        cleaned = clean(desc)
        if cleaned != desc:
            changed += 1
            updates.append((cleaned, tid))

    still_tags = sum(1 for _, d in rows if "<" in (clean(d) or ""))
    print(f"Beskrivningar: {len(rows)}, ändras: {changed}, kvarvarande '<' efter städ: {still_tags}")
    if rows:
        ex = clean(rows[0][1])
        print(f"Exempel (stycken={ex.count(chr(10)+chr(10))+1 if ex else 0}):\n---\n{ex[:300]}\n---")

    if args.apply:
        cur.executemany("UPDATE generalized_titles SET ai_description=%s WHERE id=%s", updates)
        conn.commit()
        print(f"APPLICERAT: {len(updates)} rader")
    else:
        print("DRY-RUN. Kör med --apply.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
