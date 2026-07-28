"""Slug-regler för yrkestitlar.

TVÅ regler, inte en:

1. Titel som REDAN finns i databasen  ->  ÅTERANVÄND befintlig slug.
   Regenerera aldrig. De kollapsade v1-sluggarna (t.ex. `/` och `( )` bortstrukna,
   "Administratör/Systemförvaltare" -> "administratorsystemforvaltare") är
   indexerade av Google och kanoniska. Att räkna om dem bryter SEO-kontinuiteten.

2. Titel som är NY (2026-importen)    ->  `slugify_new()`: `/` och `( )` blir
   bindestreck. Nya titlar har ingen indexhistorik att skydda, och
   "barnskotare-barnskoterska" matchar sökord bättre än "barnskotarebarnskoterska".

Import-flödet ska ALLTID gå via `resolve_slug()`, aldrig kalla `slugify_new()`
direkt på en titel som kan finnas. Regressionsvakt: `pipeline/tests/test_slugs.py`.
"""

from __future__ import annotations

import re


def slugify_new(title: str) -> str:
    """Slug för en NY titel (utan indexhistorik). Regel 2.

    Gemener; å/ä -> a, ö -> o; varje löpa av icke-alfanumeriskt (inkl. `/`,
    `(`, `)`, mellanslag) blir ETT bindestreck; ledande/eftersläpande bindestreck
    strippas. Identisk med den historiska `_employer_slug` i migrate_dump.py –
    men den regeln gäller BARA nya titlar (se resolve_slug för befintliga).
    """
    s = title.strip().lower()
    s = s.replace("å", "a").replace("ä", "a").replace("ö", "o")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def resolve_slug(title: str, existing_by_title: dict[str, str]) -> str:
    """Slug att använda vid import.

    Regel 1 vinner: finns titeln redan (nyckel i `existing_by_title`) återanvänds
    den lagrade sluggen exakt. Annars regel 2 (`slugify_new`).

    `existing_by_title` = {visningstitel: slug} från nuvarande generalized_titles.
    """
    existing = existing_by_title.get(title)
    if existing is not None:
        return existing
    return slugify_new(title)
