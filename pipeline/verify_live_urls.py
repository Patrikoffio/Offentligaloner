#!/usr/bin/env python3
"""
Go-live-test: slumpa N slugs ur databasen och verifiera att motsvarande
yrkes-URL:er svarar HTTP 200 på en given förhandsadress/produktions-URL.

Del av go-live-checklistan (SEO-kontinuitet): varje bevarad slug ska rendera.

Användning:
  python pipeline/verify_live_urls.py --base-url https://offentligaloner.vercel.app \
      [--sample 100] [--db-url ...] [--seed 0.42] [--concurrency 8]

Env: DATABASE_URL används om --db-url saknas.
Exit 0 = alla 200. Exit 1 = minst en avvikelse.
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import psycopg2
import requests


def fetch_slugs(db_url: str, sample: int, seed: float | None) -> list[str]:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    if seed is not None:
        cur.execute("SELECT setseed(%s)", (seed,))
    cur.execute(
        "SELECT slug FROM generalized_titles ORDER BY random() LIMIT %s", (sample,)
    )
    slugs = [r[0] for r in cur.fetchall()]
    conn.close()
    return slugs


def check(base_url: str, slug: str) -> tuple[str, int, str]:
    url = f"{base_url.rstrip('/')}/yrken/{slug}"
    try:
        # allow_redirects=False: en 301/302 ska INTE räknas som OK här –
        # sidan ska svara 200 direkt.
        r = requests.get(url, timeout=30, allow_redirects=False)
        return slug, r.status_code, url
    except Exception as e:  # nätverksfel
        return slug, -1, f"{url}  ({e})"


def main() -> int:
    p = argparse.ArgumentParser(description="Verifiera 200 för slumpade slugs")
    p.add_argument("--base-url", required=True)
    p.add_argument("--sample", type=int, default=100)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--seed", type=float, default=None, help="0..1 för reproducerbart urval")
    p.add_argument(
        "--db-url",
        default=os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        ),
    )
    args = p.parse_args()

    slugs = fetch_slugs(args.db_url, args.sample, args.seed)
    print(f"Testar {len(slugs)} slugs mot {args.base_url} …")

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        results = list(ex.map(lambda s: check(args.base_url, s), slugs))

    ok = [r for r in results if r[1] == 200]
    bad = [r for r in results if r[1] != 200]

    for slug, code, url in bad:
        print(f"  AVVIKELSE  HTTP {code}  {url}")

    print(f"\n200: {len(ok)}/{len(results)}   avvikelser: {len(bad)}")
    if bad:
        codes = {}
        for _, code, _ in bad:
            codes[code] = codes.get(code, 0) + 1
        print("Statuskoder bland avvikelser:", codes)
        return 1
    print("Alla slugs svarar 200 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
