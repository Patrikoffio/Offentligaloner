"""
Migrerar data från källdumpen (source_db) till v2-schemat (postgres).

Körordning:
  1. aid_labels         – från CSV-fil
  2. generalized_titles – från salary_generalizedtitle
  3. employers          – härledd ur salary_salary.employer + employer_type
  4. collection_requests + source_documents – härledd ur source_file + salary_date
  5. raw_titles         – municipality_title per employer → generalized_title
  6. salary_records     – salary_salary med sentinel-städning

Sentinel-regler (ALDRIG in i v2):
  salary_hour = -1        → hourly_salary = NULL
  employment_grade = -1   → employment_rate = NULL
  gender = 'Okänt'        → gender = NULL
  gender ∉ {K,M}          → gender = NULL  (fångar förnamn-felet)
  tomsträngar             → NULL
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import psycopg2
import psycopg2.extras

# ── Anslutningar ─────────────────────────────────────────────────────────────
SRC_DSN = "postgresql://postgres:postgres@127.0.0.1:54322/source_db"
DST_DSN = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

PROJECT_ROOT = Path(__file__).parent.parent
AID_CSV = PROJECT_ROOT / "data/stodfiler/Etikettlista-AID-2018_csv.csv"

VALID_GENDERS = {"K", "M", "Kvinna", "Man"}

# Normalisera kön → 'K'/'M'/None
def _gender(raw: str | None) -> str | None:
    if not raw or raw.strip() in ("", "Okänt"):
        return None
    s = raw.strip()
    if s in ("K", "Kvinna"):
        return "K"
    if s in ("M", "Man"):
        return "M"
    return None   # förnamn eller okänt värde → NULL


def _null(val):
    """Tomsträng → None."""
    if val is None:
        return None
    return val if str(val).strip() else None


def _employer_slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[åä]", "a", s)
    s = re.sub(r"ö", "o", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ── Steg 1: AID-etiketter ─────────────────────────────────────────────────────
def migrate_aid_labels(dst: psycopg2.extensions.connection) -> None:
    log("Steg 1: AID-etiketter")
    if not AID_CSV.exists():
        log("  VARNING: CSV-fil saknas, hoppar över aid_labels")
        return
    rows = []
    with open(AID_CSV, newline="", encoding="iso-8859-1") as f:
        reader = csv.reader(f, delimiter=";")
        # Rad 1: kolumnrubriker (rad 2 är underrubriker – hoppa den)
        headers = next(reader)
        next(reader)  # skip sub-header
        # Kolumner: "Etikett AID", "", "Beskrivning", ...
        # Rad: kod ; etikett ; beskrivning ; ...
        for parts in reader:
            if len(parts) < 2:
                continue
            code  = _null(parts[0])
            label = _null(parts[1])
            desc  = _null(parts[2]) if len(parts) > 2 else None
            if code and label:
                rows.append((code, label))
    with dst.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO aid_labels (aid_code, label) VALUES %s ON CONFLICT DO NOTHING",
            rows,
        )
    dst.commit()
    log(f"  {len(rows)} AID-etiketter importerade")


# ── Steg 2: Generaliserade titlar ─────────────────────────────────────────────
def migrate_generalized_titles(
    src: psycopg2.extensions.connection,
    dst: psycopg2.extensions.connection,
) -> dict[str, int]:
    """Returnerar {municipality_title: id} för raw_titles-steget."""
    log("Steg 2: generalized_titles")
    with src.cursor("gt_cur", cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM salary_generalizedtitle ORDER BY municipality_title")
        rows = cur.fetchall()

    inserted = 0
    with dst.cursor() as dcur:
        for row in rows:
            slug           = row["slug"] or _employer_slug(row["municipality_title"])
            title          = row["generalized_title"] or row["municipality_title"]
            if not title or not slug:
                continue
            ai_desc        = _null(row["ai_description"])
            seo_kw         = list(row["ai_keywords_seo"]) if row["ai_keywords_seo"] else None
            similar        = list(row["similar_jobs"])     if row["similar_jobs"]     else None
            muni_title     = row["municipality_title"]

            dcur.execute(
                """INSERT INTO generalized_titles (title, slug, ai_description, seo_keywords, similar_jobs)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (slug) DO NOTHING
                   RETURNING id""",
                (title, slug, ai_desc, seo_kw, similar),
            )
            inserted += dcur.rowcount

    dst.commit()
    log(f"  {inserted} generalized_titles insatta (av {len(rows)} i källan)")

    # Bygg municipality_title → generalized_title_id-mappning
    with dst.cursor() as dcur:
        dcur.execute("SELECT id, slug FROM generalized_titles")
        slug_to_id = {r[1]: r[0] for r in dcur.fetchall()}

    # Behöver municipality_title → id – hämta via slug
    with src.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT municipality_title, slug FROM salary_generalizedtitle")
        return {row["municipality_title"]: slug_to_id[row["slug"]]
                for row in cur.fetchall() if row["slug"] in slug_to_id}


# ── Steg 3: Arbetsgivare ─────────────────────────────────────────────────────
def migrate_employers(
    src: psycopg2.extensions.connection,
    dst: psycopg2.extensions.connection,
) -> dict[str, int]:
    """Returnerar {employer_name: id}."""
    log("Steg 3: employers")
    with src.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT employer, employer_type, county
            FROM salary_salary
            WHERE employer IS NOT NULL AND employer != ''
            ORDER BY employer
        """)
        rows = cur.fetchall()

    employer_id: dict[str, int] = {}
    used_slugs: set[str] = set()

    def _unique_slug(base: str) -> str:
        slug = base
        n = 2
        while slug in used_slugs:
            slug = f"{base}-{n}"
            n += 1
        used_slugs.add(slug)
        return slug

    with dst.cursor() as dcur:
        for row in rows:
            name = row["employer"].strip()
            raw_type = (row["employer_type"] or "").strip().lower()
            if "region" in raw_type:
                etype = "region"
            elif "myndighet" in raw_type or "statlig" in raw_type:
                etype = "myndighet"
            elif "bolag" in raw_type or "ab" in raw_type:
                etype = "bolag"
            else:
                etype = "kommun"
            county = _null(row["county"])
            base = _employer_slug(name)
            slug = _unique_slug(base)

            dcur.execute(
                """INSERT INTO employers (name, slug, employer_type, county)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (name) DO UPDATE SET county = EXCLUDED.county
                   RETURNING id""",
                (name, slug, etype, county),
            )
            row_id = dcur.fetchone()[0]
            employer_id[name] = row_id

    dst.commit()
    log(f"  {len(employer_id)} arbetsgivare insatta")
    return employer_id


# ── Steg 4: Insamlingsförfrågningar + källdokument ───────────────────────────
def migrate_source_documents(
    src: psycopg2.extensions.connection,
    dst: psycopg2.extensions.connection,
    employer_id: dict[str, int],
) -> dict[tuple[str, str], int]:
    """Returnerar {(employer_name, source_file): source_document_id}."""
    log("Steg 4: collection_requests + source_documents")
    with src.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT employer, source_file, salary_date, created_date
            FROM salary_salary
            WHERE employer IS NOT NULL AND employer != ''
            ORDER BY employer, source_file
        """)
        rows = cur.fetchall()

    # employer → collection_request_id (ett per arbetsgivare, år 2024)
    req_id: dict[str, int] = {}
    doc_id: dict[tuple[str, str], int] = {}

    with dst.cursor() as dcur:
        for row in rows:
            emp_name   = row["employer"].strip()
            eid        = employer_id.get(emp_name)
            if eid is None:
                continue
            source_file = row["source_file"] or ""
            salary_date = row["salary_date"]
            year        = salary_date.year if salary_date else 2024

            # collection_request – en per (employer, year)
            if emp_name not in req_id:
                dcur.execute(
                    """INSERT INTO collection_requests
                         (employer_id, collection_year, status, received_at)
                       VALUES (%s, %s, 'received', %s)
                       ON CONFLICT (employer_id, collection_year) DO UPDATE
                         SET status = EXCLUDED.status
                       RETURNING id""",
                    (eid, year, row["created_date"]),
                )
                req_id[emp_name] = dcur.fetchone()[0]

            # source_document – en per (employer, source_file)
            key = (emp_name, source_file)
            if key not in doc_id:
                dcur.execute(
                    """INSERT INTO source_documents
                         (request_id, salary_date, file_reference)
                       VALUES (%s, %s, %s)
                       RETURNING id""",
                    (req_id[emp_name], salary_date, source_file or f"{emp_name}-import"),
                )
                doc_id[key] = dcur.fetchone()[0]

    dst.commit()
    log(f"  {len(req_id)} insamlingsförfrågningar, {len(doc_id)} källdokument")
    return doc_id


# ── Steg 5: Råtitlar ─────────────────────────────────────────────────────────
def migrate_raw_titles(
    src: psycopg2.extensions.connection,
    dst: psycopg2.extensions.connection,
    employer_id: dict[str, int],
    gt_map: dict[str, int],
) -> dict[tuple[str | None, str], int]:
    """Returnerar {(employer_name_or_None, raw_title): raw_title_id}."""
    log("Steg 5: raw_titles")
    with src.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT s.employer, s.title_id, g.municipality_title
            FROM salary_salary s
            JOIN salary_generalizedtitle g ON g.municipality_title = s.title_id
            WHERE s.title_id IS NOT NULL
        """)
        rows = cur.fetchall()

    rt_id: dict[tuple[str | None, str], int] = {}
    with dst.cursor() as dcur:
        for row in rows:
            emp_name  = (row["employer"] or "").strip() or None
            raw_title = row["title_id"]
            eid       = employer_id.get(emp_name) if emp_name else None
            gt_id     = gt_map.get(raw_title)

            dcur.execute(
                """INSERT INTO raw_titles (employer_id, raw_title, generalized_title_id, mapping_method)
                   VALUES (%s, %s, %s, 'ai')
                   ON CONFLICT (employer_id, raw_title) DO NOTHING
                   RETURNING id""",
                (eid, raw_title, gt_id),
            )
            if dcur.rowcount:
                rt_id[(emp_name, raw_title)] = dcur.fetchone()[0]

        # Hämta id för alla (inkl. redan existerande)
        dcur.execute("SELECT id, employer_id, raw_title FROM raw_titles")
        emp_id_to_name = {v: k for k, v in employer_id.items()}
        for r in dcur.fetchall():
            emp_n = emp_id_to_name.get(r[1])
            key = (emp_n, r[2])
            if key not in rt_id:
                rt_id[key] = r[0]

    dst.commit()
    log(f"  {len(rt_id)} råtitlar insatta/mappade")
    return rt_id


# ── Steg 6: Löneposter ───────────────────────────────────────────────────────
def migrate_salary_records(
    src: psycopg2.extensions.connection,
    dst: psycopg2.extensions.connection,
    employer_id: dict[str, int],
    doc_id: dict[tuple[str, str], int],
    rt_id: dict[tuple[str | None, str], int],
) -> int:
    log("Steg 6: salary_records (med sentinel-städning)")
    flagged = 0
    inserted = 0
    BATCH = 2000

    with src.cursor("sal_cur", cursor_factory=psycopg2.extras.DictCursor) as scur:
        scur.execute("SELECT * FROM salary_salary ORDER BY id")

        with dst.cursor() as dcur:
            batch = []
            while True:
                rows = scur.fetchmany(BATCH)
                if not rows:
                    break
                for row in rows:
                    emp_name   = (row["employer"] or "").strip()
                    eid        = employer_id.get(emp_name)
                    if eid is None:
                        continue

                    source_file = row["source_file"] or ""
                    sdoc_id     = doc_id.get((emp_name, source_file))
                    if sdoc_id is None:
                        continue

                    raw_t = row["title_id"]
                    rt_key = (emp_name, raw_t) if (emp_name, raw_t) in rt_id \
                             else (None, raw_t)
                    raw_title_id = rt_id.get(rt_key)
                    if raw_title_id is None:
                        continue

                    # ── Sentinelrensning ───────────────────────────────────
                    sal_month = row["salary_month"]
                    sal_hour  = row["salary_hour"]
                    emp_grade = row["employment_grade"]

                    monthly = int(sal_month) if sal_month and sal_month > 0 else None
                    hourly  = float(sal_hour) if sal_hour and sal_hour > 0 else None
                    # Tim vs månad blandas ALDRIG: är personen timavlönad (hourly satt)
                    # nollas månadslönen – ett månadsvärde bredvid timlönen är en
                    # härledd/uppskattad siffra som inte får hamna i månadsstatistiken.
                    if hourly is not None:
                        monthly = None
                    # employment_grade kan vara lagrat som decimal (0–1, t.ex. 1.0 =
                    # heltid; färskt format) ELLER som procent (0–100, t.ex. 100 =
                    # heltid; äldre oktoberformat). Detektera per värde så båda funkar.
                    #   > 100  → uppenbar heltidsangivelse (t.ex. 1000) → 1.0
                    #   > 1.5  → procent → /100
                    #   annars → redan decimal (0–1)
                    if emp_grade and emp_grade > 0:
                        g = float(emp_grade)
                        if g > 100:
                            emp_rate = 1.0
                        elif g > 1.5:
                            emp_rate = round(g / 100, 3)
                        else:
                            emp_rate = round(g, 3)
                    else:
                        emp_rate = None

                    # Skydda genererat fält monthly_salary_fulltime mot overflow:
                    # numeric(10,2) klarar max ~99 999 999. Om monthly/rate > 500 000
                    # (redan flaggat) sätter vi emp_rate = NULL.
                    if monthly and emp_rate and emp_rate > 0:
                        if monthly / emp_rate > 99_999_999:
                            emp_rate = None

                    gender = _gender(row["gender"])

                    # ── Rimlighetsflaggning ────────────────────────────────
                    flag = False
                    flag_reason = None
                    if monthly and not (15_000 <= monthly <= 200_000):
                        flag = True
                        flag_reason = f"Månadslön {monthly} utanför [15000,200000]"

                    # collection_year = INSAMLINGSRUNDANS år (härleds ur created_date),
                    # inte löneperiodens år. Annars hamnar t.ex. Borås-filen (löneperiod
                    # 2023-03, insamlad 2024-11) felaktigt i en egen 2023-årsbucket.
                    _cd = row["created_date"]
                    collection_year = (
                        _cd.year if _cd
                        else (row["salary_date"].year if row["salary_date"] else 2024)
                    )

                    batch.append((
                        row["id"],          # legacy_id
                        eid,                # employer_id
                        sdoc_id,            # source_document_id
                        row["source_row_nr"],
                        collection_year,
                        row["salary_date"],
                        raw_title_id,
                        monthly,
                        hourly,
                        emp_rate,
                        _null(row["employment_type"]),
                        gender,
                        flag,
                        flag_reason,
                    ))
                    if flag:
                        flagged += 1

                if batch:
                    psycopg2.extras.execute_values(
                        dcur,
                        """INSERT INTO salary_records (
                             legacy_id, employer_id, source_document_id,
                             source_row_nr, collection_year, salary_date,
                             raw_title_id, monthly_salary, hourly_salary,
                             employment_rate, employment_type_raw, gender,
                             flagged, flag_reason
                           ) VALUES %s ON CONFLICT (legacy_id) DO NOTHING""",
                        batch,
                    )
                    inserted += len(batch)
                    batch = []
                    if inserted % 50_000 == 0:
                        dst.commit()
                        log(f"  {inserted:>7} poster insatta ...")

            dst.commit()

    log(f"  {inserted} löneposter insatta, {flagged} flaggade")
    return inserted


# ── Huvudkörning ──────────────────────────────────────────────────────────────
def main() -> None:
    log("=== Migrering startar ===")
    src = psycopg2.connect(SRC_DSN)
    dst = psycopg2.connect(DST_DSN)
    # Källdatabasen: ej autocommit — named cursors kräver en transaktion
    src.set_session(readonly=True)

    try:
        migrate_aid_labels(dst)
        gt_map     = migrate_generalized_titles(src, dst)
        emp_id     = migrate_employers(src, dst)
        doc_id_map = migrate_source_documents(src, dst, emp_id)
        rt_id_map  = migrate_raw_titles(src, dst, emp_id, gt_map)
        n          = migrate_salary_records(src, dst, emp_id, doc_id_map, rt_id_map)
        log(f"=== Migrering klar — {n} löneposter ===")
    finally:
        src.close()
        dst.close()


if __name__ == "__main__":
    main()
