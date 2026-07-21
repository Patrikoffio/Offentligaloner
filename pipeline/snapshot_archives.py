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
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
import requests

SNAPSHOT_RETENTION_DAYS = 185  # 6 månader + marginal (utgivningsbevis nr 2024-077)


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


def _parse_ts_from_name(name: str) -> datetime | None:
    """Filnamn: <YYYYMMDDTHHMMSSZ>_<sha>.json → tidsstämpel (UTC)."""
    try:
        return datetime.strptime(name.split("_", 1)[0], "%Y%m%dT%H%M%SZ").replace(
            tzinfo=timezone.utc
        )
    except (ValueError, IndexError):
        return None


def upload_to_storage(
    local_path: Path, object_name: str, base_url: str, service_key: str, bucket: str
) -> None:
    """Ladda upp snapshot till Supabase Storage (bucket privat, upsert)."""
    endpoint = f"{base_url.rstrip('/')}/storage/v1/object/{bucket}/{object_name}"
    with open(local_path, "rb") as f:
        resp = requests.post(
            endpoint,
            data=f.read(),
            headers={
                "Authorization": f"Bearer {service_key}",
                "Content-Type": "application/json",
                "x-upsert": "true",
            },
            timeout=120,
        )
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Storage-uppladdning misslyckades ({resp.status_code}): {resp.text[:300]}"
        )
    print(f"Uppladdad till Storage: {bucket}/{object_name}")


def prune_storage(base_url: str, service_key: str, bucket: str) -> None:
    """Ta bort objekt äldre än retention (behåll alltid minst 3)."""
    list_ep = f"{base_url.rstrip('/')}/storage/v1/object/list/{bucket}"
    resp = requests.post(
        list_ep,
        json={"prefix": "", "limit": 1000, "sortBy": {"column": "name", "order": "asc"}},
        headers={
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        },
        timeout=60,
    )
    resp.raise_for_status()
    names = [o["name"] for o in resp.json() if o.get("name")]
    if len(names) <= 3:
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=SNAPSHOT_RETENTION_DAYS)
    # Behåll de 3 nyaste oavsett ålder; kandidater är resten
    for name in sorted(names)[:-3]:
        ts = _parse_ts_from_name(name)
        if ts is not None and ts < cutoff:
            del_ep = f"{base_url.rstrip('/')}/storage/v1/object/{bucket}/{name}"
            d = requests.delete(
                del_ep, headers={"Authorization": f"Bearer {service_key}"}, timeout=60
            )
            if d.status_code in (200, 204):
                print(f"Tog bort gammalt Storage-objekt: {name}")


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
    parser.add_argument(
        "--supabase-url",
        default=os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
        help="Supabase projekt-URL (för Storage-uppladdning)",
    )
    parser.add_argument(
        "--service-role-key",
        default=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        help="Service-role-nyckel (för Storage-uppladdning)",
    )
    parser.add_argument(
        "--bucket", default="publication_snapshots", help="Storage-bucket för snapshots"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Hoppa över Storage-uppladdning (endast lokal snapshot)",
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

    # Ladda upp till Supabase Storage (primär arkivlagring enligt utgivningsbevis).
    # Steget får inte tyst hoppas över: saknas nycklar utan explicit --no-upload → fel.
    if args.no_upload:
        print("Storage-uppladdning överhoppad (--no-upload).")
    elif args.supabase_url and args.service_role_key:
        upload_to_storage(
            filename, filename.name, args.supabase_url, args.service_role_key, args.bucket
        )
        prune_storage(args.supabase_url, args.service_role_key, args.bucket)
    else:
        print(
            "FEL: Storage-nycklar saknas (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY). "
            "Ange dem, eller kör med --no-upload om lokal snapshot räcker.",
            file=sys.stderr,
        )
        return 2

    # Töm lokala snapshots äldre än retention (men behåll alltid minst 3 filer)
    all_snaps = sorted(snapshots_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if len(all_snaps) > 3:
        cutoff = datetime.now(timezone.utc) - timedelta(days=SNAPSHOT_RETENTION_DAYS)
        for old in all_snaps[:-3]:
            mtime = datetime.fromtimestamp(old.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                print(f"Tar bort gammal snapshot: {old.name}")
                old.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
