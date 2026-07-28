"""Regressionsvakt för slug-reglerna (pipeline/slugs.py).

Kärntestet: en titel som redan finns i databasen får ALDRIG en annan slug
efter import än före. Om någon i framtiden låter importen räkna om slugs med
bindestrecksregeln (regel 2) för befintliga titlar, byter ~985 indexerade
sidor URL – det ska fälla bygget här.

Körs med `python3 -m pytest pipeline/tests/test_slugs.py` ELLER, utan pytest,
`python3 pipeline/tests/test_slugs.py` (bygger på stdlib unittest).

Sanningskälla "före" = pipeline/tests/fixtures/existing_title_slugs.json,
ögonblicksbild av (title, slug) ur generalized_titles.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

# Importera slugs.py direkt (pipeline/ är inte ett paket – matchar repons
# fristående-skript-stil).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from slugs import resolve_slug, slugify_new  # noqa: E402

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "existing_title_slugs.json"


def _load_pairs() -> list[tuple[str, str]]:
    return [(t, s) for t, s in json.loads(FIXTURE.read_text(encoding="utf-8"))]


class ExistingTitlesKeepTheirSlug(unittest.TestCase):
    """Regel 1: befintlig titel -> återanvänd befintlig slug."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pairs = _load_pairs()
        # {titel: [alla dess befintliga slugs]} – 4 titlar har fler än en
        # (typo-/dag-natt-varianter, migration 0004 slopade UNIQUE(title)).
        cls.by_title_all: dict[str, list[str]] = {}
        for title, slug in cls.pairs:
            cls.by_title_all.setdefault(title, []).append(slug)
        # Map som import-flödet får: första sluggen per titel vinner.
        cls.by_title: dict[str, str] = {}
        for title, slug in cls.pairs:
            cls.by_title.setdefault(title, slug)

    def test_fixture_not_empty(self) -> None:
        self.assertGreater(len(self.pairs), 5000, "fixturen ser tom/trunkerad ut")

    def test_no_existing_title_gets_a_new_slug(self) -> None:
        """Varje befintligt (titel, slug)-par måste överleva importen oförändrat.

        resolve_slug ska ge en slug som REDAN finns för titeln – exakt lika för
        de 5 817 unika titlarna, och en av de befintliga för de 4 med flera slugs.
        """
        offenders = []
        for title, slug in self.pairs:
            got = resolve_slug(title, self.by_title)
            if got not in self.by_title_all[title]:
                offenders.append((title, slug, got))
        self.assertEqual(
            offenders,
            [],
            f"{len(offenders)} befintliga titlar fick en NY slug efter import "
            f"(regel 1 bruten). Exempel: {offenders[:10]}",
        )

    def test_rule1_is_load_bearing(self) -> None:
        """Bevisar att testet har tänder: ett stort antal befintliga slugs skiljer
        sig från bindestrecksregeln, så regel 1 (återanvändning) är nödvändig –
        skulle importen naivt köra slugify_new på dem byter de URL."""
        differ = sum(1 for t, s in self.pairs if slugify_new(t) != s)
        self.assertGreater(
            differ,
            500,
            "förväntade många kollapsade slugs som skiljer sig från slugify_new; "
            "annars skyddar regel 1 ingenting och testet är tandlöst",
        )


class NewTitlesUseHyphens(unittest.TestCase):
    """Regel 2: nya titlar -> `/` och `( )` blir bindestreck."""

    def test_slash_becomes_hyphen(self) -> None:
        self.assertEqual(
            slugify_new("Barnskötare/Barnsköterska"), "barnskotare-barnskoterska"
        )

    def test_parens_become_hyphen(self) -> None:
        self.assertEqual(
            slugify_new("Systemförvaltare (Gruppledare)"),
            "systemforvaltare-gruppledare",
        )

    def test_new_slug_differs_from_collapsed_v1(self) -> None:
        # Samma titel som den kanoniska "administratorsystemforvaltare", men
        # regel 2 (ny titel) ger bindestreck i stället för kollaps.
        self.assertEqual(
            slugify_new("Administratör/Systemförvaltare"),
            "administrator-systemforvaltare",
        )

    def test_swedish_letters_transliterated(self) -> None:
        self.assertEqual(slugify_new("Vårdbiträde Ängö"), "vardbitrade-ango")

    def test_no_leading_or_trailing_hyphen(self) -> None:
        self.assertEqual(slugify_new("(Vikarie)"), "vikarie")


class ResolveSlugPrefersExisting(unittest.TestCase):
    """resolve_slug: regel 1 vinner över regel 2 när titeln finns."""

    def test_existing_wins_even_if_slugify_would_differ(self) -> None:
        existing = {"Administratör/Systemförvaltare": "administratorsystemforvaltare"}
        self.assertEqual(
            resolve_slug("Administratör/Systemförvaltare", existing),
            "administratorsystemforvaltare",  # kollapsad, ej bindestreck
        )

    def test_new_title_falls_through_to_rule2(self) -> None:
        self.assertEqual(
            resolve_slug("Alldeles Ny Titel/Variant", {}),
            "alldeles-ny-titel-variant",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
