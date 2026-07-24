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

## Designsystem (v2-webb, from 2026-07-24)

Följ detta i all ny webb-UI. Ljust tema, dokumentkänsla (ingen dark mode – sajten
är innehålls-/utskriftsorienterad och lönerapporten trycks i färg). Definierat i
`web/app/globals.css` (`@theme`-tokens) – använd tokens, inte lösa hex.

**Färger (Tailwind-token → hex → användning):**
- `brand` `#0C447C` – mörkblå: ordmärke, primär knapp, rubrikaccent, band 25–75.
- `brand-mid` `#378ADD` – länkar, kategoritext, logo-stapel.
- `brand-light` `#85B7EB` – ljusblå: logo-stapel, staplar på yrkessidan.
- `accent` `#F0997B` – mjuk orange: logo-cirkel, dekor.
- `accent-strong` `#D85A30` – stark orange: nyckeltal (kommun), kommun-punkt i band.
- `accent-dark` `#993C1D` – djup orange: kommunens siffror i rapporttabellen.
- `plate-blue` `#F4F8FC` – ljusblå platta: nyckeltalskort (median/mål), stat-kort.
- `plate-orange` `#FAECE7` – ljus orange platta: nyckeltalskort (kommun).
- Band (rapport): ljusblått spann `#CFE3F6` (10–90), mörkblått `#0C447C` (25–75),
  medianlinje `#08243F`.

**Logotyp** (`web/components/Logo.tsx`, geometri låst i viewBox 64 – samma i
`app/icon.svg` favicon + `app/apple-icon.tsx` 180 px): rundad kvadrat `#0C447C`
radius 15 (~23 %); tre stigande pill-staplar (rx = halva bredden 4.5) x=13/27.5/42,
bredd 9, höjder 15/23/31 från baslinje y=49, färger `#378ADD`/`#85B7EB`/`#FFFFFF`;
orange cirkel `#F0997B` cx=46.5 cy=11 r=4. Ordmärke: "Offentliga löner" i `brand`,
weight 500, `font-sans`.

**Typografi:** `font-sans` = Geist (UI/brödtext), `font-serif` = Source Serif 4
(hero-rubrik, rapportens yrkestitel 24 px, positionsnot i kursiv). Båda via
`next/font` som CSS-variabler i `layout.tsx`. Lönevärden/nyckeltal/tabeller:
klass `.tnum` (tabulära siffror).

**Återkommande komponenter:** `SiteHeader` (alla sidor, `print:hidden`),
`DistributionBand` (spridningsband), `PaymentMarks` (endast "Säker betalning via
Stripe" – inga betalmärken; officiella brand-assets fanns ej, egna får ej ritas).
Delad copy som måste vara identisk (rapportens metodnot = om-sidans
integritetsprincip) i `web/lib/copy.ts`. Print-CSS för rapporten: `@page`-marginaler
i globals, sidbrytning per yrke (`break-before-page`), dold navigering, fast sidfot
per utskriven sida.

## Kända avvägningar

- **Sök vs. index:** autocomplete returnerar de **2 151** yrkestitlar som har
  publicerbar statistik (n≥5, `title_national_stats` inner-join), medan sitemapen
  listar **5 821** slugs inkl. **3 670** informationssidor (titlar utan n≥5-data –
  avsiktligt indexerbara för long-tail-SEO men ej sökbara). Slug = titel, inte
  titel×kommun. Avsiktligt; **se över efter SEO-stabiliseringen.**

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

## Status (uppdaterad 2026-07-23)

### RAPPORTBRYGGAN – BYGGD OCH LOKALT TESTAD GRÖN (2026-07-23)

Variant C (härdad, leveransrobust) enligt bygg-specen nedan. Byggd i web/ och
verifierad end-to-end mot lokala Supabase-stacken (identisk data som molnet):

- **Migrationer:** `0007` (purchases: report_token/selected_slugs/status/expires_at +
  idempotens-index på stripe_session), `0008` (`selected_employers bigint[]`),
  `0009` (grant select/insert/update på purchases till service_role; revoke från
  anon/authenticated – purchases bär kund-PII). **0008+0009 applicerade i MOLNET
  2026-07-23** (`supabase db push`, historik registrerad). OBS moln: service_role
  hade redan full DML via Supabase default-privilegier (permission-buggen var
  lokal-only); anon/authenticated hade FULL DML på purchases i molnet → 0009:s revoke
  var kritisk PII-härdning där (verifierat: anon läser purchases → 42501).
- **Kod:** webhook `/api/stripe-webhook` (sanningskälla, signaturverifierad, idempotent
  på stripe_session, hanterar card-sync + Klarna-async), `/api/checkout` (server-side,
  1–5 yrken × 1–5 arbetsgivare, n≥5-grind), `/api/search/titles`, `/api/report/resend`
  (rate-limitad, generiskt svar), `/api/report-status`; sidor `/rapport/[token]`,
  `/rapport/skapad`, `/rapport/avbruten`, `/rapport/skicka-igen`; beställnings-UI på
  yrkessidan (tvåstegs chips + autocomplete + kontaktrad). Mejl via Postmark
  (no-reply@offentligaloner.se), `lib/{stripe,site,email,report,ratelimit}.ts`.
- **Produktavgränsning (låst):** 39 kr = max 5 yrken × max 5 kommuner/regioner.
  Rapport = nationell spridning (referens) + tabellrader ENDAST för valda arbetsgivare
  (n≥5). Se produkttrappan under Faser (249 kr = hela landet + percentiler + uppräkning
  fas 3; offert/B2B fas 4).
- **Testköp (ENDAST LOKALT):** kort (4242) + Klarna, båda gröna – webhook 200,
  paid-rad korrekt (slugs+employers+token, giltig 92 dgr), token-rapport renderar rätt
  medianer, n≥5-filter håller, Postmark-mejl levererat externt (ej sandbox).
  Async-vägen (pending→async_payment_succeeded) + idempotens (dubbelleverans) bevisad.
  PII-skydd: anon läser purchases → 42501, skriver → 401. Granskningsskript 5/5
  (lokalt OCH mot molnet efter migreringen).
  **Molnets purchases:** en strandad TEST-rad (id 2, `cs_test_…`, 17:04) från ett
  testköp när dev pekade på molnet – ska raderas så prod-purchases börjar på 0
  (avvaktar bekräftelse). Övriga testrader finns bara lokalt.
- **PRODUKTION LIVE + SKARPT BETALFLÖDE VERIFIERAT (2026-07-23):**
  Deployad till prod på **`https://offentligaloner.vercel.app`** (`target: production`,
  READY, alias satt, startsida/yrkessidor 200). 8 env i Production scope (sk_live,
  prod-whsec, Postmark, prod-price `price_1QGSQ3…`, `NEXT_PUBLIC_SITE_URL=
  https://offentligaloner.vercel.app`, Supabase ×3). Prod-webhook mot
  `https://offentligaloner.vercel.app/api/stripe-webhook` (API 2024-06-20, tre
  checkout-event). **Skarpt 39 kr-köp (eget kort, `cs_live_`) verifierat helt:**
  webhook **200** i Stripe-dashboarden → **paid-rad i molnet** (id 3, Undersköterska ×
  Halmstad, token, 92 dgr, behålls som verifieringsköp) → **token-rapport renderar på
  prod** (ingen individdata) → **Postmark-mejl med rapportlänk mottaget**.
  Kodfix: lat Stripe-klient (`getStripe()`/`stripePriceId()`) – bygget kraschade annars
  utan runtime-secret. **DNS orört ikväll** (.se → Hetzner tills imorgon).
- **MORGONDAGENS LISTA (go-live, kör i ordning):**
  1. **DNS hos Loopia:** A `@` → `76.76.21.21`, CNAME `www` → `cname.vercel-dns.com`
     (exakt värde i Vercel → Domains). Lägg till `offentligaloner.se` + `www` i Vercel.
  2. Invänta **domänverifiering + SSL-utfärdande**.
  3. `NEXT_PUBLIC_SITE_URL` → `https://offentligaloner.se` (Production) + **redeploy**
     (annars bygger token-länkar/mejl fortsatt på vercel.app-aliaset).
  4. **Sitemap + Google Search Console:** verifiera domän, skicka in sitemap.
  5. **Ändringsanmälan till Mediemyndigheten** (serverplacering Helsingfors/Hetzner →
     Stockholm/Vercel eu-north-1). Utgivningsbevis nr 2024-077.
  6. **Inaktivera gamla Django-webhooken** (`/webhooks/stripe/` på gamla sajten) så inte
     två system svarar på samma Stripe-event. v2-webhooken (vercel.app-endpointen)
     består efter DNS – behöver ej göras om.
  7. **Revoka golive-deploytoken** (`vcp_…`, giltig 1 dag) – eller låt den löpa ut.
  8. **Hetzner-karens:** släck servern först efter DNS/SSL klart + ändringsanmälan
     inskickad; behåll karensperiod för rollback.

### POST-LAUNCH VECKA 1 (hög prio) – rapport-polish

Ordagrant enligt beställning (2026-07-23):

> Rapport-polish: (a) utseende – percentiler som staplar i print, dokumenthuvud
> med ordmärke/LÖNERAPPORT, luft mellan sektioner, diskret accentfärg på nyckeltal,
> zebrarand i arbetsgivartabellen, dölj webbläsarens URL/tidsstämpel vid utskrift
> via print-CSS; (b) förhandlingsvärde – 'Din position'-rad per vald arbetsgivare
> (delta mot riksmedian i %), infobox 'Så använder du rapporten i din
> löneförhandling' (förankra i median, 75:e percentilen som mål vid erfarenhet,
> poängtera faktiska utbetalda löner enligt offentlighetsprincipen – ej enkätdata),
> aktiva sektionsrubriker ('Så ligger lönerna i hela landet'). Ren rendering/
> print-CSS + beräkningar på befintlig data – inga schemaändringar, n≥5 orört.

_[Ingen uppräkning här – 2026-indexuppräkning hör till 249 kr-produkten, se
produkttrappan. Endast rendering/print-CSS + härledda nyckeltal ur befintliga
matviews; inga schemaändringar, n≥5-grinden orörd.]_

### ÖGONBLICKSBILD (2026-07-22)

**Klart och verifierat:**
- **Re-migrering från färsk Hetzner-dump:** 534 293 löneposter (+32 776 mot oktober,
  13 nya kommuner 2024-11-01, störst Borås 10 696), 5 821 titlar, 156 arbetsgivare.
  Migrerings-fixar för nya källformatet (employment_grade bråk↔procent, tim/månad,
  collection_year ur created_date). Migrationer 0001–0006.
- **Alla kvalitetsgrindar gröna** på nya datan (sentineler, kön K/M/NULL, rate<0.25→
  fulltime NULL, tim/månad aldrig blandat, 15k–200k-flagg, >200k-flagg).
- **Moln = lokalt** (median-hash identisk). Snapshot arkiverad.
- **SEO:** alla 5 817 live-sitemap-slugs täcks (0 saknade); 301-redirects i next.config
  (numrerade oktober-slugs + info-sidor + `/loner/:slug`→`/yrken/:slug`).
- **Kategorier:** session-5 återanvänd per slug + 38 flyttar; 8 kvar `category_reviewed=false`.
- **5 granskningsändringar:** ren ai_description (DB), aggregerad källhänvisning +
  utfällbar lista, datering, uppräknings-scaffold (bakom flagga), n<5-arbetsgivarrader.
- **Go-live-granskning KLAR** (`pipeline/granskningslista.py`, read-only, 5/5 auto-
  kontroller gröna). Manuell ögning gav 13 visningsnamn att rätta (obalanserade
  parenteser, dubbla mellanslag, stavfel Psykatrisk/Adminisrator/Modermal, Kvalité)
  → `pipeline/fix_title_typos.sql`, applicerat moln + lokalt (13+13). **Endast title,
  slugs orörda** (slug-hash oförändrad), n<5-underlag intakt. Snapshot arkiverad med
  rättade titlar (`publication_snapshots`). Steg 1–3 omkörda gröna (skript/200/301).

**Exakt läge nu:**
- Preview **deployad & Ready** (target=preview, skyddad – senaste `offentligaloner-ou8nini21`,
  deploy8, verifierad target=preview + publikt alias 404). Nås SSO-inloggad som patrikoffio.
- **Publika aliaset `offentligaloner.vercel.app` = 404** (ej exponerat).
- **Uppräkningsflaggan `NEXT_PUBLIC_SHOW_PROJECTION_2026` = AV** tills avtalstalen i
  `web/lib/projections.ts` är ifyllda och granskade.
- **Vercel-token är kortlivad** → varje ny deploy/promote kräver en FÄRSK token
  (den förra gick ut mitt i en deploy). Projekt: `prj_E1yb55HDSKzTGxZW9TlirGprl53Q`,
  team patrikoffio; env-värden finns i `web/.env.local`.

**Kvar hos verksamheten (ej blockerande):** ompröva de 8 `category_reviewed=false`,
fyll i avtalstal + aktivera uppräkningsflaggan, städa Hetzner `/tmp`.

### GO-LIVE-SEKVENS (steg för steg)

**0. BLOCKERANDE – RAPPORTBRYGGA (nytt, före promote/DNS):**
Gamla sajten har ett aktivt **betalt rapportflöde som genererar intäkter idag** och
saknas i v2. Go-live är PAUSAD tills v2 har en minimal motsvarighet. Gamla flödet är
kravkälla. Kartlagt (2026-07-22, read-only mot offentligaloner.se):
- Ingång: yrkessidor `/loner/<slug>`, checkboxar → välj upp till 5 befattningar,
  val i `sessionStorage._x_selected_titles` (Alpine.js).
- CTA "Jag är nyfiken!": htmx `hx-post /create-checkout-session/` → **Stripe Checkout**.
- Pris: **39 kr/rapport** (engångs), **119 kr/månad** (abonnemang). Rapport giltig 3 mån.
- Leverans: HTML-"LÖNERAPPORT" (allmänt, antal, lönespridning för valda befattningar);
  `/exempel-rapport/` = demo. `/rapport` ger 404 (levereras via genererad URL efter köp).
- ⚠️ Gamla exempelrapporten visar **n<5** (n=1,2,3,4 med medianer) → v2-bryggan MÅSTE
  filtrera **n≥5** (hård regel 1) och aldrig visa individdata.
- Okänt utan källkod: exakt Stripe-fulfillment/webhook, success/cancel-URL, hur köpt
  rapport persisteras/hämtas (3 mån), 39 kr vs 119 kr-logik.
**BESLUT (2026-07-22): variant C, härdad.** Krav på bygg-specen (inget byggs före
godkänd spec):
- Checkout Session skapas **server-side** (API-route). **Webhook (signaturverifierad)
  är leveransens sanningskälla** — Klarna är asynkron och kunden kan stänga fliken före
  retur, så success-sidan får INTE vara enda leveransväg. (Reviderat 2026-07-23; tidigare
  "ingen webhook i v1" ersatt.) Ingen leverans på blott retur-URL utan bekräftad betalning.
- **Tokenserad rapport-URL** (slumpad token, lagrad i `purchases`, **3 mån** giltighet),
  visas efter köp + skickas till kundens mejl (enklaste transaktionsmejl; kräver det ny
  tjänst → föreslå och invänta ok).
- Rapporten byggs **enbart ur matviews (n≥5)**, max **5** valda titlar, med
  källhänvisning + metodnot i rapporten. Aldrig individdata.
- **Stripe secret + service-role endast server-side**, aldrig i klientbundeln.
- **Pris 39 kr oförändrat. Inget abonnemang** i denna iteration.
#### RAPPORTBRYGGA – LÅSTA DETALJER + BYGG-SPEC (handover 2026-07-23)

Källa: read-only-extrakt ur `offlon_prod_web` (Django 5.0.6, stripe 9.10.0).

**Gamla flödet (låst):**
- Val på yrkessida → `sessionStorage._x_selected_titles` (Alpine), max 5 titlar.
  "Jag är nyfiken!" = htmx `hx-post /create-checkout-session/`, `product=nyfiken`.
- `CreateStripeCheckoutSessionView`: skapar Order(status=pending) + Stripe Checkout
  Session, `HX-Redirect` till Stripe. Validerar 1–5 titlar.
- **Stripe price (PROD, product=nyfiken): `price_1QGSQ3LNrfBYc0eaEvsidyX0`** (=39 kr,
  beloppet ligger i Stripe). Test/DEBUG: nyfiken `price_1PaZ8OLNrfBYc0eaTIUJ3hDs`,
  ekonomisk (119 kr abo, EJ live i prod) `price_1PPFj6LNrfBYc0ea5V2fBMPV`.
- Session-config: `mode='payment'`, **`payment_method_types=['card','klarna']`**,
  `automatic_tax.enabled=True`, `locale='sv'`, `consent_collection.terms_of_service`,
  `custom_text` (ångerrätts-waiver, digital tjänst levereras omedelbart),
  `allow_promotion_codes=True`, `metadata={selected_titles, order_id}`.
  `success_url=/lyckat?order_id=<order.order_id>`, `cancel_url=/avbryt`.
- **Fulfillment via WEBHOOK** `/webhooks/stripe/` (checkout.session.completed):
  skapar user (konto+aktiveringsmejl), `WebReport(titles_array, expiry=now+3mån)`,
  `send_confirmation_email`, Celery `warm_cache`. → v2 SKA INTE använda webhook (v1).
- **Rapport `/rapport/<id>/`**: LOGIN-gated (owner==user), byggs ur RÅA
  `Salary`-rader (`report_context(salaries)`, `report_template_web.html`) → **läcker
  n<5** (exempelrapport visar n=1,2,3,4). v2 SKA i stället bygga ur matviews n≥5.
- **Mejl: Postmark** (`EMAIL_BACKEND=anymail.backends.postmark`, `from
  no-reply@offentligaloner.se`), EJ SendGrid (sendgrid-paket finns men oanvänt).
  → v2 återanvänder Postmark-kontot/servertoken, ingen ny tjänst.

**`purchases`-schemat idag:** id, email, product, generalized_title_id, employer_id,
amount_sek, stripe_session, created_at. Saknar: report_token, selected_slugs (multi),
expires_at, status → **migration 0007** krävs.

**ENV (server-side, ALDRIG NEXT_PUBLIC):** `STRIPE_SECRET_KEY` (test+prod separat),
`STRIPE_WEBHOOK_SECRET` (test+prod separat – egen signeringshemlighet per miljö;
webhook-endpointen registreras i Stripe-dashboarden för BÅDA miljöerna, exakta
instruktioner ges vid det steget), `POSTMARK_SERVER_TOKEN`, `SUPABASE_SERVICE_ROLE_KEY`
(finns). Rapport-render + purchases-skrivning + mejl sker server-side.

**BYGG-SPEC v2 (variant C, härdad + leveransrobust) – BYGG I DENNA ORDNING:**
1. **Migration 0007 (VISA SQL FÖRST, invänta ok):** utöka `purchases`: `report_token
   text unique`, `selected_slugs text[]`, `status text`, `expires_at timestamptz`
   (befintliga: email/product/amount_sek/stripe_session/created_at). Ingen individdata.
2. **Webhook `/api/stripe-webhook` = SANNINGSKÄLLA:** verifiera signatur mot
   `STRIPE_WEBHOOK_SECRET`. På `checkout.session.completed` OCH
   `checkout.session.async_payment_succeeded` (Klarna async) → skapa purchases-rad
   (report_token=slumpad 32 byte hex, selected_slugs ur metadata, expires_at=now+3mån,
   email ur customer_details, status=paid), **idempotent på stripe_session**, skicka
   Postmark-mejl med token-URL + utgångsdatum. (Hantera även async_payment_failed →
   status=failed.)
3. **`/api/checkout` (server-side):** validera 1–5 slugs med n≥5 (title_national_stats);
   Stripe Checkout Session (`price_1QGSQ3LNrfBYc0eaEvsidyX0`, `['card','klarna']`,
   automatic_tax, locale sv, consent/ångerrätt, metadata=selected_slugs);
   `success_url=/rapport/skapad?session_id={CHECKOUT_SESSION_ID}`,
   `cancel_url=/rapport/avbruten`. Returnera session.url.
4. **UI:**
   - Beställningskomponent på yrkessidan: kryssa upp till 5 titlar (klientstate),
     "Beställ lönerapport (39 kr)" → `/api/checkout`.
   - `/rapport/skapad` (**snabbväg, ej enda väg**): finns purchases-rad för session_id
     → visa token-länk; annars "rapporten mejlas när betalningen bekräftats" (Klarna
     kan dröja) + kort pollning/uppmaning att kolla mejlen.
   - `/rapport/avbruten`.
   - **`/rapport/skicka-igen`**: ange e-post → ommejla giltiga (ej utgångna)
     rapportlänkar för adressen. **Rate-limitad** (ingen läckage/enumeration).
   - `/rapport/[token]` (server-side): slå upp purchases på token (404 annars),
     expires_at<now → utgången; rendera ur matviews (title_national_stats +
     title_employer_stats), n≥5, max 5, sektioner Allmänt/Antal/Lönespridning + källa
     + metodnot; **print-CSS** (utskrift/spara-som-PDF); **utgångsdatum synligt**.
     Ingen inloggning (token=access), ingen individdata.
5. **Mejl (Postmark, server-side):** köpbekräftelse + token-URL + **utgångsdatum (3 mån)**,
   from no-reply@offentligaloner.se. Samma Postmark-konto som gamla sajten.

**Behövs från Patrik före bygge:** Stripe secret key test+prod, `STRIPE_WEBHOOK_SECRET`
test+prod (efter endpoint-registrering), bekräfta `price_1QGSQ3…` = 39 kr aktiv,
Postmark server-token + avsändardomän. Beslut: tokenserad rapport (INGA kundkonton/
aktiveringsmejl som gamla flödet).

**RADERA-LISTA Hetzner** (fråga före radering): `/tmp/fresh_salaries_*.dump`,
`/tmp/dump_on_server.sh`, `/tmp/diagnose_server.sh`, `/tmp/extract_django_source.sh`,
`/tmp/offlon_source_*.txt`, `/tmp/offlon_diag_*.txt`.

Först därefter (efter godkänd+byggd rapportbrygga):

0b. **Rapportbryggans migrationer i MOLNET – KLART 2026-07-23.**
   0008 (`selected_employers bigint[]`) + 0009 (grants) applicerade via `supabase db
   push`, historik registrerad, verifierat (kolumn `_int8`, anon/authenticated-grants
   återkallade). En strandad test-rad (id 2) i moln-`purchases` ska raderas → prod
   börjar på 0. **Kvar (blockerande före promote):** molnets env-värden nedan +
   prod-Stripe-nycklar + skarp webhook-registrering.
   Sätt molnets env: `STRIPE_SECRET_KEY` (prod sk_live), `STRIPE_WEBHOOK_SECRET`
   (prod, efter endpoint-registrering i Stripe), `STRIPE_PRICE_ID=price_1QGSQ3…`,
   `POSTMARK_SERVER_TOKEN`, `POSTMARK_FROM`, `NEXT_PUBLIC_SITE_URL=https://offentligaloner.se`.

1. **Omgranskning** av preview: data, yrkessidor, redirects (301), footer med
   utgivningsbevis, källhänvisningar, **rapportflödet** (beställnings-UI, checkout,
   webhook-leverans, token-rapport, skicka-igen).
2. **Promote till production:** `vercel deploy --prod` (med färsk token). Sajten blir
   publik på *.vercel.app.
3. **Vercel → Project → Domains:** lägg till `offentligaloner.se` + `www.offentligaloner.se`.
4. **Loopia DNS:** A-post `@` → **76.76.21.21**; CNAME `www` → **cname.vercel-dns.com**
   (exakt värde visas i Vercel Domains). Invänta domänverifiering + SSL-utfärdande.
5. **Ändringsanmälan till Mediemyndigheten:** serverplacering Helsingfors/Hetzner →
   Stockholm/Vercel (eu-north-1). Utgivningsbevis nr 2024-077.
6. **Hetzner-karens:** säg upp/släck servern FÖRST efter att DNS pekar rätt, SSL är
   utfärdat och ändringsanmälan inskickad. Behåll karensperiod (rollback-möjlighet)
   innan servern faktiskt släcks.

### Fas 1 (klar – siffror uppdaterade efter re-migrering 2026-07-22)
Dump migrerad till v2-schemat och verifierad grön. **Efter re-migrering från färsk
dump:** 534 293 rader, 156 arbetsgivare, 5 821 slugs totalt, 2 151 titlar med
publicerbar data (n≥5). (Oktober-migreringen gav 501 517 / 145 / 5 654 / 2 116.)

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
- **Granskningsfynd (5 ändringar) deployade till skyddad preview:** (1) ai_description
  städad i DB (`clean_ai_descriptions.py`, 5 820 rader moln+lokalt), render delar på
  tomrad; (2) källhänvisning aggregerad rad + utfällbar lista (matview 0006
  `title_employer_all`); (3) datering "2024 års insamling / augusti 2026"; (4)
  uppräkning 2024→2026 bakom feature-flagga `NEXT_PUBLIC_SHOW_PROJECTION_2026` (AV;
  tal i `web/lib/projections.ts` fylls i separat); (5) n<5-arbetsgivare visas med
  antal utan lönevärden. Verifierat lokalt + deployat (deploy Ready, target=preview,
  publikt alias 404). Vercel-token förnyad (förra gick ut mitt i deploy).
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
### PRODUKTTRAPPA (låst avgränsning)

Tre nivåer, tydligt åtskilda så 39 kr-rapporten inte kannibaliserar de dyrare:

- **39 kr – Lönerapport (byggd, rapportbryggan):** avgränsad till **max 5 yrken ×
  max 5 valda kommuner/regioner** (min 1 vardera). Innehåll: per yrke nationell
  lönespridning som referens + tabellrader ENDAST för de valda arbetsgivarna
  (n≥5-regeln oförändrad). Ingen uppräkning, inga fullständiga uttag. Tokenserad,
  giltig 3 mån. Diskret kontaktrad i beställnings-UI:t för behov utanför trappan.
- **249 kr – Förhandlingsunderlag (fas 3):** **hela landet** (alla arbetsgivare, inte
  bara 5) + fulla **percentiler**. **KÄRNFUNKTIONEN är 2026-indexuppräkningen** enligt
  centrala avtal (`web/lib/projections.ts` + flaggan NEXT_PUBLIC_SHOW_PROJECTION_2026) –
  det är det som motiverar priset. Nedladdningsbar PDF: valda yrken × kommuner, 2024
  uppmätt + 2026 uppskattad, per titel/arbetsgivare, med metodnot och källhänvisning.
  **Grindar innan flaggan slås på (alla tre måste vara gröna):**
  1. **Avtalstal ifyllda och källbelagda** per avtalsområde i `web/lib/projections.ts`
     (`AGREEMENT_INCREASE`) – varje procenttal ska ha en angiven källa (avtalstext/datum).
  2. **Granskad mappning yrke → avtalsområde** (`CATEGORY_TO_AGREEMENT`): Kommunal,
     Vårdförbundet, Vision m.fl. har **olika avtal och olika revisionsdatum** – mappningen
     måste stämmas av mot rätt avtalsområde per yrke/kategori, inte schabloniseras.
  3. **Presenteras ALLTID som uppskattning med avtalskälla, aldrig som faktisk lön** –
     i både PDF-rapporten och på sajten. Formuleringen ska vara otvetydig (uppskattat
     värde enligt centralt avtal X, revision Y), så det aldrig läses som uppmätt lön.
  **Teaser-not:** överväg att visa en **uppräknad median som teaser i 39 kr-rapporten
  FÖRST när 249-produkten finns och är live** – annars kannibaliseras trappan (39-kr
  ger då bort kärnvärdet i 249-kr gratis).
- **Offert / B2B (fas 4):** fullständiga datauttag, datalicenser, "Utvald arbetsgivare",
  myndighetsexpansion, Platsbanken-integration. Hanteras som offert, inte självbetjäning.

- **Fas 3:** Stripe: förhandlingsunderlag 249 kr (se produkttrappan ovan), datalicenser.
- **Fas 4:** Offert/B2B, Platsbanken-integration, "Utvald arbetsgivare", myndighetsexpansion.
