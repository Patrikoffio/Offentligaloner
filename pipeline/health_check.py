#!/usr/bin/env python3
"""pipeline/health_check.py — snabb hälsokontroll av produktion + repo.

Körs UTAN argument. Skriver "OK" eller "VARNING" per kontroll och avslutar med
exit 1 om någon kontroll gav VARNING (annars 0).

DB-url läses från DATABASE_URL — SAMMA env-variabel som snapshot_archives.py.
INGEN fallback: health-check frågar "är produktionen i synk?" och måste därför
köras mot MOLNET. Mot en lokal DB svarar den på fel fråga (och kan råka matcha).
Saknas DATABASE_URL avbryts körningen med instruktion. Live-sajten läses från
NEXT_PUBLIC_SITE_URL / SITE_URL (standard https://offentligaloner.se).

Kontroller:
  1. Migrationer registrerade i molnet (supabase_migrations.schema_migrations)
  2. Antal rader i title_national_stats vs senaste snapshot
  3. sitemap.xml: antal /yrken/-<loc> vs antal titlar med statistik
  4. /yrken/controller: median på sidan vs databasens median
  5. git status: ocommittat? vilken branch?
  6. Senaste GSC-export äldre än 14 dagar?
"""

import glob
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

REPO = Path(__file__).resolve().parent.parent
DB_URL = os.getenv("DATABASE_URL")  # ingen fallback – måste peka på molnet
SITE = (
    os.getenv("NEXT_PUBLIC_SITE_URL")
    or os.getenv("SITE_URL")
    or "https://offentligaloner.se"
).rstrip("/")
GSC_MAX_AGE_DAYS = 14

_results: list[bool] = []


def record(name: str, ok: bool, detail: str) -> None:
    print(f"{'OK     ' if ok else 'VARNING'}  {name}: {detail}")
    _results.append(ok)


def http_get(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "offlon-healthcheck"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ── 1. Migrationer ──────────────────────────────────────────────────────────
def check_migrations(cur) -> tuple[bool, str]:
    local = sorted(
        {Path(p).name.split("_", 1)[0] for p in glob.glob(str(REPO / "supabase/migrations/*.sql"))}
    )
    if not local:
        return False, "inga lokala migrationsfiler hittade"
    cur.execute("SELECT version FROM supabase_migrations.schema_migrations")
    cloud = {row[0] for row in cur.fetchall()}
    missing = [v for v in local if v not in cloud]
    if missing:
        return False, f"saknas i molnets migrationshistorik: {', '.join(missing)}"
    return True, f"alla {len(local)} migrationer registrerade i molnet"


# ── 2. Rader vs snapshot ────────────────────────────────────────────────────
def check_snapshot(cur) -> tuple[bool, str]:
    cur.execute("SELECT count(*) FROM title_national_stats")
    db_n = cur.fetchone()[0]
    snaps = sorted(glob.glob(str(REPO / "snapshots/*.json")))
    if not snaps:
        return False, "ingen snapshot hittad i snapshots/"
    latest = snaps[-1]  # filnamn börjar med tidsstämpel → sorterbart
    with open(latest, encoding="utf-8") as f:
        snap_n = len(json.load(f).get("title_national_stats", []))
    name = Path(latest).name
    if db_n == snap_n:
        return True, f"{db_n} rader = senaste snapshot ({name})"
    return False, f"DB {db_n} rader ≠ senaste snapshot {name} ({snap_n})"


# ── 3. sitemap <loc> vs titlar med statistik ────────────────────────────────
def check_sitemap(cur) -> tuple[bool, str]:
    xml = http_get(f"{SITE}/sitemap.xml")
    yrken = [u for u in re.findall(r"<loc>(.*?)</loc>", xml) if "/yrken/" in u]
    cur.execute("SELECT count(*) FROM title_national_stats")
    stats = cur.fetchone()[0]
    if len(yrken) == stats:
        return True, f"{len(yrken)} /yrken/-loc = {stats} titlar med statistik"
    return False, f"{len(yrken)} /yrken/-loc ≠ {stats} titlar med statistik"


# ── 4. /yrken/controller: median på sidan vs DB ─────────────────────────────
def check_controller(cur) -> tuple[bool, str]:
    cur.execute(
        """
        SELECT round(tns.median)::int
        FROM title_national_stats tns
        JOIN generalized_titles gt ON gt.id = tns.generalized_title_id
        WHERE gt.slug = 'controller'
        """
    )
    row = cur.fetchone()
    if not row:
        return False, "controller saknar statistik i databasen"
    db_med = row[0]
    html = http_get(f"{SITE}/yrken/controller")
    tmatch = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    scope = tmatch.group(1) if tmatch else html
    m = re.search(r"median\s+([\d\s  ]+?)\s*kr", scope, re.I)
    if not m:
        return False, "hittar ingen median i sidans titel"
    page_med = int(re.sub(r"\D", "", m.group(1)))
    if page_med == db_med:
        return True, f"median {db_med} kr matchar sidan"
    return False, f"DB median {db_med} ≠ sidans {page_med}"


# ── 5. git ──────────────────────────────────────────────────────────────────
def check_git() -> tuple[bool, str]:
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=REPO
    ).decode().strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=REPO
    ).decode().strip()
    if dirty:
        return False, f"branch '{branch}', {len(dirty.splitlines())} ocommittade ändringar"
    return True, f"branch '{branch}', arbetsträd rent"


# ── 6. GSC-export ålder ─────────────────────────────────────────────────────
def check_gsc() -> tuple[bool, str]:
    patterns = [
        str(REPO / "data" / "**" / "*gsc*"),
        str(REPO / "data" / "**" / "*Performance*"),
        str(Path.home() / "Downloads" / "*Performance-on-Search*"),
        str(Path.home() / "Downloads" / "gsc*.csv"),
    ]
    files = [f for pat in patterns for f in glob.glob(pat, recursive=True) if Path(f).is_file()]
    if not files:
        return False, "ingen GSC-export hittad (data/ eller ~/Downloads)"
    newest = max(files, key=lambda f: Path(f).stat().st_mtime)
    age = (datetime.now(timezone.utc).timestamp() - Path(newest).stat().st_mtime) / 86400
    if age > GSC_MAX_AGE_DAYS:
        return False, f"senaste ({Path(newest).name}) är {age:.0f} dgr gammal (>{GSC_MAX_AGE_DAYS})"
    return True, f"senaste ({Path(newest).name}) {age:.0f} dgr gammal"


def main() -> int:
    if not DB_URL:
        print(
            "FEL: DATABASE_URL är inte satt.\n"
            "Health-check ska köras mot MOLNET – annars svarar den på fel fråga\n"
            "(en lokal DB kan råka matcha och ge falskt OK).\n"
            "Sätt den till molnets anslutningssträng och kör igen, t.ex.:\n"
            "  DATABASE_URL='postgresql://<user>:<lösenord>@<host>:5432/postgres' \\\n"
            "    python3 pipeline/health_check.py",
            file=sys.stderr,
        )
        return 2

    conn = None
    cur = None
    try:
        conn = psycopg2.connect(DB_URL)
        conn.autocommit = True  # read-only → undvik txn-abort-kaskad
        cur = conn.cursor()
    except Exception as e:
        record("0. DB-anslutning", False, f"{e.__class__.__name__}: {e}")

    def run(name: str, fn, *args) -> None:
        try:
            ok, detail = fn(*args)
        except Exception as e:
            ok, detail = False, f"fel: {e.__class__.__name__}: {e}"
        record(name, ok, detail)

    db_checks = [
        ("1. Migrationer i molnet", check_migrations),
        ("2. title_national_stats vs snapshot", check_snapshot),
        ("3. sitemap <loc> vs titlar med statistik", check_sitemap),
        ("4. /yrken/controller median vs DB", check_controller),
    ]
    for name, fn in db_checks:
        if cur is None:
            record(name, False, "hoppar över – ingen DB-anslutning")
        else:
            run(name, fn, cur)

    run("5. git status", check_git)
    run("6. GSC-export ålder", check_gsc)

    if conn is not None:
        conn.close()

    n_warn = sum(1 for ok in _results if not ok)
    print()
    if n_warn:
        print(f"VARNING: {len(_results) - n_warn}/{len(_results)} gröna, {n_warn} varning(ar).")
    else:
        print(f"OK: {len(_results)}/{len(_results)} gröna.")
    return 1 if n_warn else 0


if __name__ == "__main__":
    sys.exit(main())
