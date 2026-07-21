"""Parser-template för Offentligalöner.se.

Kopiera denna fil till pipeline/parsers/<arbetsgivare>_<år>.py för varje nytt
filformat. Varje parser läser en utlämnad fil och returnerar rader i det
gemensamma målformatet (SalaryRow). Se CLAUDE.md → "Datakvalitetsregler vid import".

Regler som gäller ALLA parsers:
- Rådata ändras aldrig; parsern läser från data/ och skriver till databasen.
- Sentineler (-1, 'Okänt', tomsträng, '#SAKNAS') blir None – aldrig magiska värden.
- Könsfältet kan innehålla förnamn (känt fel): allt utom K/M/Kvinna/Man/Okänt
  loggas och blir None. Personnamn får aldrig nå databasen.
- Timavlönade: hourly_salary sätts och monthly_salary är None – blanda aldrig.
- Orimliga månadslöner (<15000 eller >200000) → flagged=True med flag_reason.
- Varje parser har ett pytest-test mot en anonymiserad fixture i tests/fixtures/.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterator

import openpyxl


@dataclass
class SalaryRow:
    """Gemensamt målformat – speglar salary_records i databasen."""

    source_row_nr: int
    raw_title: str
    monthly_salary: float | None
    hourly_salary: float | None
    employment_rate: float | None
    employment_type_raw: str | None
    gender: str | None            # 'K' | 'M' | None
    age: int | None
    department: str | None        # förvaltning
    workplace: str | None         # placering/tjänsteställe
    aid_code: str | None
    salary_supplements: float | None
    tenure_years: float | None
    flagged: bool = False
    flag_reason: str | None = None


SENTINELS = {"", "-1", "-1.0", "-1.00", "#saknas", "n/a", "na", "okänt", "okand"}


def clean(value) -> str | None:
    """Normalisera cellvärde: sentineler och tomt → None."""
    if value is None:
        return None
    s = str(value).strip()
    return None if s.lower() in SENTINELS else s


def parse_gender(value) -> tuple[str | None, str | None]:
    """Returnerar (kön, flaggorsak). Fångar förnamn i könskolumnen."""
    s = clean(value)
    if s is None:
        return None, None
    low = s.lower()
    if low in {"k", "kvinna", "female", "f"}:
        return "K", None
    if low in {"m", "man", "male"}:
        return "M", None
    # Okänt värde – kan vara ett personnamn. Logga ALDRIG själva värdet i klartext
    # till databasen; endast att det förekom.
    return None, "ogiltigt könsvärde ersatt med NULL"


def parse_file(path: Path, salary_date: date) -> Iterator[SalaryRow]:
    """Anpassa kolumnmappningen här för respektive arbetsgivares format."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    header_skipped = False
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if not header_skipped:
            header_skipped = True
            continue

        # ---- ANPASSA KOLUMNINDEX PER ARBETSGIVARE ----
        raw_title = clean(row[0])
        salary = clean(row[1])
        rate = clean(row[2])
        # ----------------------------------------------

        if raw_title is None:
            continue

        gender, gflag = parse_gender(row[3] if len(row) > 3 else None)

        monthly = float(salary) if salary else None
        flagged, reason = False, gflag
        if monthly is not None and not (15_000 <= monthly <= 200_000):
            flagged, reason = True, f"orimlig månadslön: {monthly}"

        yield SalaryRow(
            source_row_nr=i,
            raw_title=raw_title,
            monthly_salary=monthly,
            hourly_salary=None,
            employment_rate=float(rate) if rate else None,
            employment_type_raw=None,
            gender=gender,
            age=None,
            department=None,
            workplace=None,
            aid_code=None,
            salary_supplements=None,
            tenure_years=None,
            flagged=flagged,
            flag_reason=reason,
        )
