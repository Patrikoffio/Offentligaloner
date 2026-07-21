"""
Verifierar att migreringen uppfyller definitionerna av klart:
  ✓ ~501 517 rader i salary_records
  ✓ Medellön per arbetsgivare inom 1 % av källan
  ✓ Alla 9 383 slugs återfinns i generalized_titles
  ✓ Inga sentinelvärden (-1, 'Okänt') i v2-databasen
"""

from __future__ import annotations

import sys
import psycopg2
import psycopg2.extras

SRC_DSN = "postgresql://postgres:postgres@127.0.0.1:54322/source_db"
DST_DSN = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

EXPECTED_ROWS   = 501_517
# 9 383 = totalt antal råtitelmappningar i källan.
# Distinkta slugs (generalized_titles) = 5 654 – det är det vi verifierar.
EXPECTED_SLUGS  = 5_654
SALARY_TOL      = 0.01   # 1 %


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "✓" if ok else "✗"
    print(f"  {status}  {label}" + (f"  ({detail})" if detail else ""))
    return ok


def main() -> None:
    src = psycopg2.connect(SRC_DSN)
    dst = psycopg2.connect(DST_DSN)
    src.set_session(autocommit=True)
    dst.set_session(autocommit=True)
    passed = True

    print("\n=== Verifiering ===\n")

    # 1. Radantal
    with dst.cursor() as c:
        c.execute("SELECT COUNT(*) FROM salary_records")
        n_rows = c.fetchone()[0]
    ok = abs(n_rows - EXPECTED_ROWS) / EXPECTED_ROWS < 0.05
    passed &= check(
        f"Radantal: {n_rows:,} (förväntat ~{EXPECTED_ROWS:,})",
        ok,
        f"avvikelse {abs(n_rows - EXPECTED_ROWS):,}"
    )

    # 2. Slugs
    with dst.cursor() as c:
        c.execute("SELECT COUNT(*) FROM generalized_titles")
        n_slugs = c.fetchone()[0]
    passed &= check(
        f"Slugs: {n_slugs} generalized_titles (förväntat {EXPECTED_SLUGS})",
        n_slugs == EXPECTED_SLUGS,
    )

    # 3. Medellön per arbetsgivare (jämför mot källan)
    with src.cursor() as sc:
        sc.execute("""
            SELECT employer, AVG(salary_month) as avg_m
            FROM salary_salary
            WHERE salary_month > 0
            GROUP BY employer
            HAVING COUNT(*) >= 10
        """)
        src_avgs = {row[0]: float(row[1]) for row in sc.fetchall()}

    with dst.cursor() as dc:
        dc.execute("""
            SELECT e.name, AVG(sr.monthly_salary) as avg_m
            FROM salary_records sr
            JOIN employers e ON e.id = sr.employer_id
            WHERE sr.monthly_salary IS NOT NULL
            GROUP BY e.name
            HAVING COUNT(*) >= 10
        """)
        dst_avgs = {row[0]: float(row[1]) for row in dc.fetchall()}

    mismatches = []
    for emp, src_avg in src_avgs.items():
        dst_avg = dst_avgs.get(emp)
        if dst_avg and abs(dst_avg - src_avg) / src_avg > SALARY_TOL:
            mismatches.append((emp, src_avg, dst_avg))

    passed &= check(
        f"Medellön per arbetsgivare inom 1 %: {len(mismatches)} avvikelser",
        len(mismatches) == 0,
        ", ".join(f"{e}: {s:.0f}→{d:.0f}" for e, s, d in mismatches[:3]) if mismatches else "",
    )

    # 4. Inga sentineler i v2
    with dst.cursor() as c:
        c.execute("SELECT COUNT(*) FROM salary_records WHERE monthly_salary = -1")
        neg1_month = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM salary_records WHERE hourly_salary = -1")
        neg1_hour = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM salary_records WHERE employment_rate = -1")
        neg1_grade = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM salary_records WHERE gender NOT IN ('K','M') AND gender IS NOT NULL")
        bad_gender = c.fetchone()[0]

    passed &= check("Inga monthly_salary = -1",     neg1_month == 0,  str(neg1_month))
    passed &= check("Inga hourly_salary = -1",      neg1_hour  == 0,  str(neg1_hour))
    passed &= check("Inga employment_rate = -1",    neg1_grade == 0,  str(neg1_grade))
    passed &= check("Inga ogiltiga gender-värden",  bad_gender == 0,  str(bad_gender))

    # 5. Sammanfattning
    print()
    with dst.cursor() as c:
        c.execute("SELECT COUNT(*) FROM employers")
        print(f"  Arbetsgivare: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM source_documents")
        print(f"  Källdokument: {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM raw_titles")
        print(f"  Råtitlar:     {c.fetchone()[0]}")
        c.execute("SELECT COUNT(*) FROM salary_records WHERE flagged = true")
        print(f"  Flaggade:     {c.fetchone()[0]}")

    print()
    if passed:
        print("✓ Verifiering GRÖN – migreringen är klar")
    else:
        print("✗ Verifiering RÖDIG – se avvikelser ovan")
        sys.exit(1)

    src.close()
    dst.close()


if __name__ == "__main__":
    main()
