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

## Status (uppdaterad 2026-07-21)

### Fas 1 (klar)
Dump migrerad till v2-schemat och verifierad grön:
501 517 rader, 145 arbetsgivare, 5 654 slugs totalt, 2 116 titlar med publicerbar data (n≥5)
efter migration 0002.

### Fas 1b (pågår)

#### Klart i session 3 (2026-07-21)
- employment_rate-verifiering: fördelning ren (67 % heltid, 23 % NULL, 0 ogiltiga).
- Sidgenerering: generateStaticParams hämtar ALLA 5 654 slugs (paginerat, 1 000/batch).
- Snapshot-arkivering: `pipeline/snapshot_archives.py` exporterar nationell statistik
  (2 116 rader) + per-arbetsgivare (9 411 rader) till JSON med SHA+tidsstämpel.

#### Klart i session 4 (2026-07-21)
- Migration 0002: employment_rate < 0.25 → monthly_salary_fulltime = NULL.
  Effekt: Skolläkare p90 373k→185k, Danspedagog 167k→69k. 6 titlar tappar n≥5-status.
- Informationssidor för titlar utan data: kategoristatistik, 3–5 similar_jobs-länkar,
  förklaringstext. Bygget grön: 5 658 sidor utan TS-fel.

#### Klart i session 5 (2026-07-21)
- Kategoriomklassning klar och godkänd. Alla 5 654 titlar semantiskt klassade i
  de 24 kategorierna från Grupper.txt. Flermanuell granskning: tre stickprov á 30,
  riktad genomgång av Ekonomi och Administration (1 414→967 efter rättningar),
  5 manuellt korrigerade gränsfall. Slutlig fördelning:
    Utbildning och Pedagogik 1 020, Ekonomi och Administration 967,
    Vård och Omsorg 801, Samhällsbyggnad och Infrastruktur 484,
    Socialt arbete och Stöd 441, Kultur och Fritid 356, IT och Digitalisering 307.
  Kommunövergripande 2 515 → 30. Folkhälsa (ny) 31. Alla 24 kategorier representerade.
  Applicerat till generalized_titles. Sidor rebuiltade: 5 658 sidor, grön.

#### Session 6 – RE-MIGRERING från färsk dump (2026-07-22)
Färska Hetzner-dumpen visade sig ha **534 293 löneposter (+32 776)** och **9 778
titlar (+395)** – data importerades efter oktober (13 nya kommuner 2024-11-01,
störst Borås 10 696). Radantalsjämförelsen i steg 5 fångade inte att slug/titel-
VÄRDEN också ändrats (live-sajten städade titlar). Därför full re-migrering:
- Django-appen kör Docker Swarm; db-containern lyssnar på **PGPORT 5454**, användaren
  ligger i Docker-secret `/run/secrets/POSTGRE_USER`, pg_hba `local=trust`.
  `dump_on_server.sh` byggd deterministiskt kring detta (efter iterativ serverdiagnos).
- `migrate_dump.py`-fixar för nya källformatet: employment_grade är nu **bråk**
  (1.0=heltid) inte procent → formatdetektering (annars blev all fulltime NULL);
  tim vs månad blandas aldrig (hourly satt → monthly NULL, 3 047 timavlönade);
  collection_year ur created_date (insamlingsrunda) → Borås i 2024 inte egen 2023.
- Migration **0003** (återkalla anon/authenticated-grants) + **0004** (slopa
  UNIQUE(title) – flera slugs kan dela visningsnamn). Båda i moln + lokalt.
- Kategorier: regelbaserad baseline + **överlagring av session-5:s granskade
  kategorier ur molnet per slug** (5 404 återanvända). 417 genuint nya på
  regelbaserad – 173 i Ekonomi, många felklass (3D-Utvecklare→IT, Ambulanspersonal
  →Vård, Badmästare→Kultur…). **Gränsfallsgranskning kvar (användaren).**
- B (received_at) + C (>200k-flagg) omkörda. Verifiering grön: moln = lokalt
  (534 293 / 5 821 / national 2 151 / employer 9 815), median-hash identisk.
- **SEO: alla 5 817 live-sitemap-slugs täcks nu av v2 (0 saknade).** next.config:
  248 st 301 för retirerade numrerade oktober-slugs (råtitel-mappade) + info-sidor
  + generell `/loner/:slug`→`/yrken/:slug` (explicit statusCode 301). Lokalt
  verifierat via next start: 100/100 slumpade + 60/60 tidigare saknade → 200,
  redirects 301. Ny snapshot arkiverad.
- **Deployad och verifierad mot molndata:** Vercel-prod-deploy (5 825 sidor) live på
  https://offentligaloner.vercel.app. 200-test mot deployen: **100/100 slumpade +
  alla 416 tidigare saknade → 200**. Redirects **301** (struktur/numrerad/info).
  Footer med utgivningsbevis renderar. (OBS: aliaset är publikt igen efter deploy –
  ta ned inför beslut om go-live-timing, samma som tidigare.)
- **Kategori-gränsfall KLART:** 38 flyttar applicerade (30 säkra + 8 tveksamma med
  `category_reviewed=false`, migration 0005). Ekonomi 1 110→1 035. Deployad (deploy4),
  nya kategorier verifierade live (Veterinär→Vård, Parkskötare→Miljö). `diagnos.txt`
  borttagen.
- **Vercel återuppsatt i förhandsläge (skyddad preview):** nytt projekt
  `prj_E1yb55HDSKzTGxZW9TlirGprl53Q` (team patrikoffio), 3 env-vars satta för
  preview+production. Deployad (build grön, samma verifierade data/kod). Det publika
  production-aliaset `offentligaloner.vercel.app` **borttaget (`vercel alias rm`) →
  404**; deployen finns kvar och granskas via den **SSO-skyddade** unika adressen
  (kräver inloggning som patrikoffio). Inget publikt exponerat.
  **Go-live:** `vercel deploy --prod` (eller `vercel alias set <deploy> offentligaloner.se`)
  + DNS-flytt. Env-värden finns i `web/.env.local` om projektet behöver återskapas.
- **Fix ai_description-rendering:** beskrivningarna är lagrade som HTML (`<p>…</p>`)
  och renderades som råtext (taggar syntes). Åtgärdat vid rendering (ej datamutation):
  `descriptionParagraphs`/`descriptionPlain` i yrkessidan delar i stycken + strippar
  taggar; meta-description som plain text. Övriga fält rena. Omdeployad som äkta
  preview (target=preview, publikt alias fortsatt 404).
- **KVAR (användaren):** `/tmp` på Hetzner-servern att städa (fresh-dump + skript);
  ev. omprövning av de 8 `category_reviewed=false`-titlarna.

#### Klart i session 6 – go-live (2026-07-21, PÅ OKTOBER-DATA – ersatt av re-migreringen ovan)
- **Steg 1 – molnprojekt kopplat.** Supabase eu-north-1, projekt-ref
  `usiruoserwsymxzmnfeg`. Anslutning sker via session-poolern
  `aws-0-eu-north-1.pooler.supabase.com:5432` (direkt-hosten är IPv6-only och
  onåbar från körmiljön/containern). `web/.env.local` pekar på molnet (lokala
  dev-värden kvar utkommenterade). Migrationer 0001+0002 pushade
  (`supabase db push --db-url`), historik registrerad.
- **Data migrerad lokalt → moln** via `pg_dump -Fc --data-only --schema=public`
  (exkl. matview-data) + `pg_restore --single-transaction`. Verifiering grön:
  alla 9 bastabeller identiska (salary_records 501 517), title_national_stats
  2 116 med identiska medianer, title_employer_stats 9 370 bit-för-bit identisk.
  Enda avvikelse: p90 på 2/2 116 rader skiljer ~1e-10 (double-precision
  percentile_cont, summeringsordning ändras vid restore) – rundas bort vid
  visning, ingen datadifferens. Matviews refreshade i molnet efter load.
- **Steg 2 – snapshot → Supabase Storage.** Privat bucket `publication_snapshots`
  skapad. `snapshot_archives.py` utökad med `upload_to_storage` + `prune_storage`
  (6-mån retention, behåller min 3). Steget kan inte tyst hoppas över: saknas
  SUPABASE_URL/SERVICE_ROLE_KEY utan explicit --no-upload → exit 2. Körd mot
  molnet: 2 116 nationella + 9 370 per-arbetsgivare, objekt verifierat i bucketen.
- **Steg 3 – Vercel-deploy.** Projekt `offentligaloner` (team patrikoffio) länkat,
  rot = `web/`. Env-vars (URL, anon, service-role) satta för preview+production;
  service-role används endast vid build (generateStaticParams), följer ej med till
  klient. Deploy grön: 5 658 sidor. Förhandsadress: https://offentligaloner.vercel.app
  (produktions-alias, publikt 200; hash-baserade deployment-URL:er är SSO-skyddade).
  Yrkessida verifierad mot molndata + footer (utgivningsbevis nr 2024-077,
  ansvarig utgivare Patrik Larsson). OBS: vercel.app-aliaset är publikt nåbart –
  ingen custom domain kopplad än, offentligaloner.se orörd. Footer fanns redan
  komplett i layout.tsx (renderas på varje sida).
- **Steg 4 – 200-test.** `pipeline/verify_live_urls.py` (slumpar N slugs ur DB,
  kräver HTTP 200 utan redirect). 100/100 slugs → 200 mot förhandsadressen.
- **Steg 5 – färsk Hetzner-dump: KLAR.** Gamla servern kör Docker Swarm
  (`offlon_prod_*`); Django-DB:n har egen POSTGRES_USER (ej 'postgres') och
  ligger bredvid postgres_exporter + umami-analytics. `fetch_hetzner_dump.sh`
  (automatik) + `dump_on_server.sh` (plan B, körs på servern) dumpar via
  containerns egna creds över lokal socket. Färsk dump: salary_salary **501 517**,
  salary_generalizedtitle **9 383** – IDENTISKT med oktober-baslinjen. Enligt
  radantals-kriteriet: ingen omkörning av migreringen behövs, v2-datan är färsk.
  OBS: den fysiska färska dumpen ligger kvar på Hetzner `/tmp` (scp-hemtagning
  utfördes ej) – hämta hem den som go-live-arkiv innan servern släcks om så önskas.
- Temp-DB `oct_baseline`/`fresh_verify` + `/tmp/oct.dump`/`/tmp/data.dump` i lokala
  containern städade. (`/tmp/salaries.dump` från tidigare session lämnad orörd.)

### Go-live-förberedelse KOMPLETT (session 6)
Steg 1–5 gröna. Deployment Protection kan ej aktiveras på Vercel Hobby (kräver
Pro) → produktions-deployen NEDTAGEN (`vercel remove`), `offentligaloner.vercel.app`
ger 404 tills skarp go-live. Projekt/länkning/env-vars behållna.

**Kvarstår inför skarp go-live (manuella beslut/åtgärder):**
1. ~~Granskning av molndata~~ KLAR (se nedan). Sid-/SEO-granskning pågår
   (slug-avstämning + 301-redirects, BLOCKERANDE före DNS-flytt).
2. Promote av produktions-deployen (`vercel deploy --prod`).
3. DNS-flytt hos Loopia (offentligaloner.se → Vercel).
4. Ändringsanmälan till Mediemyndigheten (serverplacering Helsingfors → Stockholm/
   Vercel), därefter uppsägning av Hetzner.

#### Granskning molndata (session 6) – KLAR
20+ kontroller mot hårda regler + datakvalitet, grönt: publiceringsgrind (min n=5),
kön endast K/M/NULL, noll sentinelläckage, RLS default-deny (inga policies),
vyn exkluderar flaggade rader, tim/månad ej blandat, 5 654 unika slugs, 24 kategorier
(0 NULL), källhänvisning 100 % täckt, allt collection_year=2024. Åtgärdat:
- **A. Migration 0003**: återkallade anon/authenticated-grants på salary_records,
  raw_titles, collection_requests, source_documents (djupförsvar utöver RLS).
  Applicerad moln + lokalt, service_role orörd.
- **B. Backfill received_at** (`pipeline/backfill_received_at.py`): 3 ur Kommunlista
  2024 (kol "mottagen lönelista", giltiga datum), 157 ur filnamnsdatum, 0 föll till
  lönedatum. Alla 160 källdok har nu utlämningsdatum (moln + lokalt).
- **C. Flaggade 86 rader** med heltidsekv. lön > 200 000 (låg grad × normal lön;
  `pipeline/flag_fulltime_over_200k.sql`). Ej cappat. Vyer refreshade: national kvar
  2 116, employer 9 370→9 369, inga titlar tappade n≥5. Effekt: Medicinsk Rådgivare
  p90 190 160→113 540, Skolläkare 185 000→172 900. Ny snapshot arkiverad.
- **D.** Små-n seniora roller (Regiondirektör n=6 m.fl.) – noterat, uppfyller n≥5.

#### Återstår i 1b
- Mappningstäckning via AI-klassning (mapping_method='ai', reviewed=false).
- Go-live-checklista: färsk Hetzner-dump, verifiering grön, snapshot-pipeline kopplad
  till Supabase Storage, footeruppgifter kontrollerade, 301-redirects testade, DNS-flytt,
  ändringsanmälan Mediemyndigheten, Hetzner uppsagt.

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
