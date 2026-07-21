#!/usr/bin/env python3
"""
Snapshot-arkivering av publika aggregat – krav enligt utgivningsbevis nr 2024-077.

Vid varje refresh av materialiserade vyer + deploy sparas en JSON-snapshot av
title_national_stats och title_employer_stats till:
  - Lokalt: snapshots/<SHA>_<timestamp>.json  (primär, alltid)
  - Supabase Storage (bucket: publication_snapshots): planerat fas 1b/go-live

Kör som sista steg i deploy-pipeline – ska INTE kunna hoppas över.

Användning:
  python pipeline/snapshot_archives.py [--sha GIT_SHA] [--snapshots-dir PATH]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras


def get_git_sha(fallback: str = "unknown") -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode()
            .strip()
        )
    except Exception:
        return fallback


_NUMERIC_COLS = ("mean_salary", "p10", "p25", "median", "p75", "p90")


def _to_float(d: dict) -> dict:
    for key in _NUMERIC_COLS:
        if key in d and d[key] is not None:
            d[key] = float(d[key])
    return d


def fetch_national_stats(cur: psycopg2.extensions.cursor) -> list[dict]:
    cur.execute("""
        SELECT
            tns.generalized_title_id,
            gt.title,
            gt.slug,
            gt.category,
            tns.collection_year,
            tns.n,
            tns.mean_salary,
            tns.p10,
            tns.p25,
            tns.median,
            tns.p75,
            tns.p90
        FROM title_national_stats tns
        JOIN generalized_titles gt ON gt.id = tns.generalized_title_id
        ORDER BY tns.n DESC
    """)
    cols = [d.name for d in cur.description]
    return [_to_float(dict(zip(cols, row))) for row in cur.fetchall()]


def fetch_employer_stats(cur: psycopg2.extensions.cursor) -> list[dict]:
    cur.execute("""
        SELECT
            tes.generalized_title_id,
            gt.title,
            gt.slug,
            tes.employer_id,
            e.name AS employer_name,
            tes.collection_year,
            tes.n,
            tes.mean_salary,
            tes.p10,
            tes.p25,
            tes.median,
            tes.p75,
            tes.p90,
            tes.latest_source_date::text AS latest_source_date
        FROM title_employer_stats tes
        JOIN generalized_titles gt ON gt.id = tes.generalized_title_id
        JOIN employers e ON e.id = tes.employer_id
        ORDER BY tes.generalized_title_id, tes.n DESC
    """)
    cols = [d.name for d in cur.description]
    return [_to_float(dict(zip(cols, row))) for row in cur.fetchall()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Skapa aggregat-snapshot (arkiveringskrav)")
    parser.add_argument("--sha", default=None, help="Git SHA (auto-detekteras om saknas)")
    parser.add_argument(
        "--snapshots-dir",
        default=str(Path(__file__).parent.parent / "snapshots"),
        help="Lokal katalog för snapshots (skapas om saknas)",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@127.0.0.1:54322/postgres",
        ),
        help="PostgreSQL-anslutningssträng",
    )
    args = parser.parse_args()

    sha = args.sha or get_git_sha()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshots_dir = Path(args.snapshots_dir)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    print(f"Ansluter till databasen…")
    try:
        conn = psycopg2.connect(args.db_url)
    except Exception as e:
        print(f"FEL: Kan inte ansluta till databasen: {e}", file=sys.stderr)
        return 1

    cur = conn.cursor()

    print("Hämtar title_national_stats…")
    national = fetch_national_stats(cur)
    print(f"  {len(national)} rader")

    print("Hämtar title_employer_stats…")
    employer = fetch_employer_stats(cur)
    print(f"  {len(employer)} rader")

    conn.close()

    snapshot = {
        "schema_version": 1,
        "deploy_sha": sha,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "title_national_stats": national,
        "title_employer_stats": employer,
    }

    filename = snapshots_dir / f"{ts}_{sha}.json"
    print(f"Skriver snapshot → {filename}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, default=str)

    size_mb = filename.stat().st_size / 1_048_576
    print(f"Klar. Storlek: {size_mb:.1f} MB")
    print(f"Titlar nationellt: {len(national)}, per arbetsgivare: {len(employer)}")

    # Töm snapshots äldre än 6 månader (men behåll alltid minst 3 filer)
    all_snaps = sorted(snapshots_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if len(all_snaps) > 3:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=185)  # 6 månader + marginal
        for old in all_snaps[:-3]:
            mtime = datetime.fromtimestamp(old.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                print(f"Tar bort gammal snapshot: {old.name}")
                old.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
