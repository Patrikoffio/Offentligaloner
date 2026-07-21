# Offentligalöner.se – projektinstruktioner

Lönestatistik för svensk offentlig sektor, insamlad via offentlighetsprincipen och
publicerad under utgivningsbevis. Detta är INTE ett greenfield-projekt: en Django-baserad
föregångare finns i drift med ~501 000 löneposter (2024) och 9 383 generaliserade titlar
med AI-beskrivningar, SEO-nyckelord och slugs. Vi bygger v2 och migrerar in allt.

## Arkitektur (v2)

- **Databas:** Postgres via Supabase. Migrationer i `supabase/migrations/`.
  Målschema: `0001_initial_schema.sql` – läs den innan datamodellen rörs.
- **Webb:** Next.js (App Router) på Vercel, statisk generering av yrkes-, arbetsgivar-
  och kommunsidor. SEO är primär trafikkanal.
- **Pipeline:** Python 3.12 i `/pipeline`. En parser per arbetsgivarformat.
- **Betalningar (fas 3):** Stripe Checkout.

## KRITISKT: SEO-kontinuitet vid migrering

- Slugs i `generalized_titles` kopieras EXAKT från gamla `salary_generalizedtitle.slug`.
- Alla gamla URL:er som ändrar struktur får 301-redirect i `next.config`.
- AI-beskrivningar, SEO-nyckelord och similar_jobs migreras – de är befintligt innehåll,
  generera inte om dem utan explicit beslut.

## Klassificering: AID, inte SSYK

Kommuner/regioner klassar enligt SKR:s AID 2018 (252 etiketter, tabell `aid_labels`).
2025 års begäran inkluderar AID-etikett per anställd – mappa direkt när den finns.
SSYK finns som valfri kolumn för framtida SCB-jämförelser; bygg inget på den ännu.
Yrkeskategorier för navigering: de 24 grupperna i `generalized_titles.category`
(Vård och Omsorg, Utbildning och Pedagogik, IT och Digitalisering, ...).

## Datamigrering från dumpen (första pipeline-jobbet)

Källa: `20241027_backup_salaries.dump` (Postgres 16, custom format).

1. `salary_generalizedtitle` → `generalized_titles` + `raw_titles`
   (municipality_title = råtitel, generalized_title = publikt namn, slug bevaras).
2. `salary_salary` → `employers`, `collection_requests`, `source_documents`
   (härleds ur source_file + salary_date), `salary_records` (legacy_id = gammalt id).
3. Sentineler blir NULL: `-1` i salary_hour/employment_grade, `'Okänt'` i gender,
   tomsträngar. Sentineler får ALDRIG överleva in i v2.
4. `employment_type` är fri text från varje arbetsgivare ("1 Tillsvidare",
   "1 (Tills vidare)", "SÄVATIM ...") → spara rått i salary_records.employment_type_raw
   och normalisera via `employment_type_mappings`.
5. Verifiera efter migrering: radantal, medellön per arbetsgivare inom 1 % mot
   källdatabasen, samtliga 9 383 slugs återfinns.

## Insamlingsprocessen (2025 och framåt)

- Kommunlista/Regionlista-arken ersätts av tabellen `collection_requests` – bygg ett
  enkelt internt admin-gränssnitt för statusuppdatering i fas 2.
- Begäran enligt mall i `/docs/mallar/` (uppdaterad enligt "Tänka på till 2025"):
  utbildningsnivå UTGÅR, in: ålder, förvaltning, placering/tjänsteställe, AID-etikett,
  lönetillägg, avlöningsform. Motivera med utgivningsbevis.
- Verkligheten per arbetsgivare loggas: taxa, avslag, e-legitimationskrav, vägrar
  digitalt. Detta är affärskritisk processkunskap.
- Statliga myndigheter (Myndigheter.xlsx, `employers.include`) är expansionslistan.

## Datakvalitetsregler vid import

- Könsfältet kan innehålla förnamn (känt fel i utlämnade filer). Städsteget ska
  detektera icke-värden (allt utom K/M/Kvinna/Man/Okänt), logga och sätta NULL.
  PERSONNAMN FÅR ALDRIG NÅ DATABASEN.
- Månadslön < 15 000 eller > 200 000 SEK → flagga, importera inte automatiskt.
- Timavlönade: hourly_salary sätts, monthly_salary NULL – blanda aldrig.
- Sysselsättningsgrad saknas → NULL + employment_rate_assumed hanteras i statistikvyn
  (endast poster med känd heltidslön räknas).
- Dubbletter inom samma källdokument (identisk rad exkl. source_row_nr) → flagga.
- Ny arbetsgivarfil: kopiera `pipeline/parsers/_template.py`, skriv fixture-test,
  provimportera lokalt, rimlighetsgranska antal + medellön före produktion.

## Kodkonventioner

- Tabell-/kolumnnamn engelska snake_case; svensk domänkommentar i migrationen.
- TypeScript strict; typer via `supabase gen types`.
- Python: type hints, ruff, pytest per parser.
- Commits på svenska, imperativ.
- Inga hemligheter i repo. `/data` (rådata med persondata) är gitignorad.

## Utgivningsbevis (nr 2024-077, giltigt t.o.m. 2034-10-28) – systemkrav

Databasen "Offentliga löner, offentligaloner.se" har utgivningsbevis från
Mediemyndigheten. Detta ger kraven nedan – de är juridiska skyldigheter, inte önskemål:

- **Obligatoriska uppgifter på sajten:** databasens namn, tillhandahållare och
  ansvarig utgivare (Patrik Larsson) ska stå tydligt på startsidan eller under
  Kontakt. Renderas i footern på varje sida, hårdkodat i layoutkomponenten.
- **Arkivering:** allt publicerat innehåll ska sparas i 6 månader efter borttagning,
  och varje ändring i databasen ska sparas. Implementation:
  (a) sajtinnehåll versioneras i git – ingen publicering utanför git,
  (b) vid varje refresh av materialiserade vyer + deploy sparas en snapshot av de
  publika aggregaten (`publication_snapshots`-bucket i Supabase Storage, JSON per
  vy + deploy-SHA + tidsstämpel), retention minst 6 månader efter ersättning.
  Snapshotsteget är en del av deploy-pipelinen och får inte kunna hoppas över.
- **Serverplacering:** beviset anger idag server i Helsingfors och att överföringar
  utgår från Sverige. Supabase-projektet skapas i region eu-north-1 (Stockholm).
  Ändringsanmälan görs till Mediemyndigheten när Hetzner släcks – checkpunkt i
  go-live-listan.
- **Endast verksamheten ändrar innehållet** (enligt teknisk beskrivning i beviset):
  ingen användargenererad data (inlämnade löner, kommentarer) får byggas utan att
  beviset först ändras och innehållet avskiljs. Blockerande juridisk grind för
  sådana features.

## Hårda regler (gäller alltid, inga undantag)

1. Aggregat med n < 5 publiceras aldrig – filtret sitter i de materialiserade vyerna.
2. Individdata exponeras aldrig publikt. Feature-flagga `EXPOSE_INDIVIDUAL_DATA`
   (default false) gate:ar all individvisning.
3. Källhänvisning + utlämningsdatum renderas ur `source_documents` under varje tabell.
4. Rådatafiler i `/data` läses, ändras aldrig.
5. Ingen deploy utan aggregat-snapshot (arkiveringsskyldigheten ovan).

## Faser

- **Fas 1:** Migrera dumpen till v2-schemat (färsk dump från Hetzner före go-live),
  importera 2025-filer, ~50 statiska yrkessidor live med bevarade slugs + redirects.
  Go-live-checklista: verifiering grön, snapshot-pipeline aktiv, footeruppgifter på
  plats, DNS omdirigerad, ändringsanmälan till Mediemyndigheten skickad, Hetzner
  uppsagd först därefter.
- **Fas 2:** Full sidgenerering (titel × arbetsgivare), sök, admin för
  collection_requests, insamlingsrunda 2026.
- **Fas 3:** Stripe: lönerapport 39 kr, förhandlingsunderlag 249 kr, datalicenser.
- **Fas 4:** Platsbanken-integration, "Utvald arbetsgivare", myndighetsexpansion.
