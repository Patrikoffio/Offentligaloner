# Offentligalöner.se – v2

Lönestatistik för svensk offentlig sektor. Läs `CLAUDE.md` först – den styr allt
arbete i detta repo.

## Struktur

```
CLAUDE.md                    Projektinstruktioner (läses av Claude Code)
supabase/migrations/         Databas-schema (0001_initial_schema.sql = målmodellen)
data/dump/                   Postgres-dump från befintlig produktion (gitignorad)
data/stodfiler/              AID-etiketter, grupper, kommunlistor, titelgeneralisering
data/2024/, data/2025/       Utlämnade lönefiler per arbetsgivare (gitignorade)
docs/mallar/                 Begäranmallar (2025-mallen är den aktuella)
pipeline/parsers/            En parser per arbetsgivarformat (_template.py = utgångspunkt)
pipeline/tests/fixtures/     Anonymiserade testfiler
web/                         Next.js-appen (skapas i Fas 1)
```

## Kom igång

Förkrav: Node 20+, Python 3.12, Docker Desktop (för lokal Supabase), Supabase CLI.

Första sessionen i Claude Code:

> Läs CLAUDE.md noggrant. Fas 1 börjar nu. Initiera git, sätt upp lokal Supabase
> och kör migrationen. Skriv sedan migreringsskriptet som flyttar dumpen i
> data/dump/ till v2-schemat enligt migreringsplanen i CLAUDE.md, inklusive
> sentinel-städning och verifieringssteget. Visa mig din plan innan du börjar bygga.

OBS: `data/` är gitignorad eftersom den innehåller persondata. Säkerhetskopiera
den separat (den ingår inte i git-historiken).
