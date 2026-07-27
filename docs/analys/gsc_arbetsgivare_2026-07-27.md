# GSC- och arbetsgivaranalys — 2026-07-27

Read-only-analys (ingen kod ändrad). Två delar: (1) Google Search Console-trafik
korsad mot databasens sidor, (2) arbetsgivartyper och kommuntäckning.

## Källor

- **GSC:** `data/gsc_sidor_16mn.csv` (Search Console → Prestanda → Sidor-export,
  uppackad ur `~/Downloads/offentligaloner.se-Performance-on-Search-2026-07-27.zip`).
  Intervall **2025-03-26 → 2026-07-25** (~16 mån). `Diagram.csv` i samma zip ger
  property-totalen.
- **Databas:** Supabase (moln), `generalized_titles` + `title_national_stats`
  (collection_year 2024).
- **Befolkning:** SCB folkmängd 31 dec 2024, joinad på kommunkod.
- **Arbetsgivare:** `employers` + `salary_records`.

---

## Del 1 — GSC × databasen

### Täckningsvarning (viktig)

GSC:s sid-export är hårdcappad till **1000 rader**. Filen har **999 sidor =
46 050 klick**, vilket är **69 % av property-totalen 66 674 klick** (16 mån).
Resterande **~20 624 klick** ligger i en svans av lågtrafiksidor som exporten
inte listar — **den är omätt**. www/non-www är hopslagna → 839 unika sidor.

### Grupper

Sida = yrkessida vars slug finns i DB. "Med data" = slug i `title_national_stats`
(n≥5, 2024). "Utan data" = slug finns i `generalized_titles` men saknar n≥5
(informationssida).

| Grupp | Sidor | Klick | Visningar | CTR | Medelpos |
|---|--:|--:|--:|--:|--:|
| Med lönedata | 438 | 26 602 | 800 669 | 3,32 % | 19,5 |
| **Utan lönedata (info)** | 399 | 18 172 | 488 604 | 3,72 % | 21,8 |
| Yrke, slug ej i DB (301) | 1 | 39 | 3 772 | 1,03 % | 33,3 |
| Startsida + statisk | 1 | 1 237 | 12 588 | 9,83 % | 17,9 |

- **Andel klick från datalösa sidor: 39,5 % av exportens klick** (18 172 / 46 050).
  Mot hela property blir uppmätt andel 27,3 % — men det är ett undervärde eftersom
  svansens datalösa klick inte räknas i täljaren.
- Info-sidorna har **högre CTR (3,72 %) än datasidorna (3,32 %)** — de rankar på
  nischade long-tail-frågor med låg konkurrens.

### 30 datalösa sidor med flest klick (16 mån)

| # | Klick | Visn | CTR | Pos | Sida |
|--:|--:|--:|--:|--:|---|
| 1 | 367 | 9954 | 3,7 % | 11,2 | /loner/lararvikarie |
| 2 | 306 | 1840 | 16,6 % | 15,1 | /loner/psykologassistent |
| 3 | 297 | 1597 | 18,6 % | 4,7 | /loner/heltidsmentor |
| 4 | 260 | 6130 | 4,2 % | 32,5 | /loner/chief-information-security-officer-ciso |
| 5 | 208 | 5462 | 3,8 % | 24,3 | /loner/ledningskoordinator |
| 6 | 179 | 1495 | 12,0 % | 11,3 | /loner/sspf-koordinator |
| 7 | 166 | 1605 | 10,3 % | 17,8 | /loner/arbetsmiljostrateg |
| 8 | 161 | 3097 | 5,2 % | 15,7 | /loner/sarskilt-kvalificerad-kontaktperson |
| 9 | 160 | 5577 | 2,9 % | 37,7 | /loner/hallbarhetscontroller |
| 10 | 156 | 2516 | 6,2 % | 7,4 | /loner/dataskyddssamordnare |
| 11 | 147 | 2297 | 6,4 % | 6,9 | /loner/skiftledare |
| 12 | 147 | 4632 | 3,2 % | 15,1 | /loner/senior-advisor |
| 13 | 144 | 1713 | 8,4 % | 8,8 | /loner/vardhundsforare |
| 14 | 139 | 877 | 15,8 % | 7,5 | /loner/elanlaggningsansvarig |
| 15 | 132 | 993 | 13,3 % | 5,9 | /loner/valsamordnare |
| 16 | 131 | 2338 | 5,6 % | 9,4 | /loner/elansvarig |
| 17 | 130 | 2195 | 5,9 % | 13,1 | /loner/elsakerhetsansvarig |
| 18 | 129 | 2640 | 4,9 % | 49,1 | /loner/objektledare |
| 19 | 129 | 2754 | 4,7 % | 21,3 | /loner/socialt-ansvarig-socionom-sas |
| 20 | 128 | 610 | 21,0 % | 5,0 | /loner/valsamordnareutredare |
| 21 | 124 | 3060 | 4,1 % | 14,2 | /loner/digital-transformationsledare |
| 22 | 121 | 4720 | 2,6 % | 9,5 | /loner/beredskaps-och-sakerhetssamordnare |
| 23 | 115 | 4035 | 2,9 % | 7,9 | /loner/overformyndarhandlaggare-arbetsplatsledare |
| 24 | 114 | 3659 | 3,1 % | 30,4 | /loner/vice-vdkoncernstrateg |
| 25 | 109 | 5910 | 1,8 % | 10,3 | /loner/lss-chef |
| 26 | 108 | 1498 | 7,2 % | 23,6 | /loner/underhallssamordnare |
| 27 | 107 | 13326 | 0,8 % | 19,6 | /loner/facility-manager |
| 28 | 106 | 930 | 11,4 % | 12,9 | /loner/forskningskoordinator |
| 29 | 105 | 797 | 13,2 % | 7,4 | /loner/kris-och-beredskapsstrateg |
| 30 | 104 | 2523 | 4,1 % | 21,1 | /loner/sakerhetsskyddschef-bitradande |

### Steg 3 — förlust vid noindex på alla datalösa sidor

**Intervall: ~30–45 % av organisk trafik, troligast ~40 %.** I klick:

- **Hård golvsiffra (endast uppmätt):** 18 172 klick / 16 mån ≈ **13 600 klick/år**.
- **Realistiskt (inkl. omätt svans):** ~24 000–30 000 / 16 mån ≈ **18 000–22 000 klick/år**.

Scenarier för hur svansens 20 624 klick fördelas mellan data/info:

| Antagande om svansen | Total datalös | Andel av property | Per år |
|---|--:|--:|--:|
| Speglar exporten (40,6 % info) | ~26 500 | 40 % | ~19 900 |
| Skevar mot info (55 %) | ~29 500 | 44 % | ~22 100 |
| Skevar mot data (30 %) | ~24 400 | 37 % | ~18 300 |

**Osäkerheter (störst först):**

1. **1000-radscappen.** 31 % av klicken ligger utanför exporten och deras
   data/info-split är uppskattad, inte mätt. Info-sidor är fler (3 670 mot 2 151)
   och rankar sämre → svansen skevar troligen mot info, mot övre delen av
   intervallet. **Stängs av en query-nivå-export eller GSC-API-uttag utan cap.**
2. **Andra ordningens effekter.** Noindex på tunna sidor kan höja kvalitetssignaler
   och frigöra crawl-budget → en del trafik kan omfördelas till kvarvarande sidor
   snarare än försvinna. Nettoförlust kan bli lägre än brutto.
3. **Mängden är inte statisk.** Efter 2026 års insamling passerar en del
   info-titlar n≥5 och blir datasidor — bör inte noindexas. Beslutet bör villkoras.
4. Klassificeringen exkluderar startsida/statiska sidor (behålls indexerade);
   www/non-www hopslagna.

**Slutsats:** datalösa sidor bär i storleksordningen 4 av 10 organiska klick.
Total noindex är avfärdad — för dyr. Kvarvarande, mildare fråga: noindexa bara
sidor som **både** saknar data **och** saknar klick (t.ex. < 3 klick/16 mån).
Det kräver query-/sid-nivå-export utan 1000-cap för att identifieras säkert.

---

## Del 2 — Arbetsgivartyper och kommuntäckning

### Arbetsgivartyper

Schemat tillåter `kommun/region/myndighet/bolag`. I datan finns bara två:

| Typ | Arbetsgivare | Individer |
|---|--:|--:|
| Kommun | 149 | 441 671 |
| Region | 7 | 92 622 |
| Kommunalförbund | 0 | 0 |
| Kommunalt bolag | 0 | 0 |
| Statlig myndighet | 0 | 0 |

Inga kommunalförbund (t.ex. räddningstjänstförbund), inga kommunala bolag, inga
statliga myndigheter. De tre är expansionsspår, ej insamlade.

### Befolkningsviktad kommuntäckning

Befolkning 2024 (SCB) som proxy för antal anställda. Alla 149 DB-kommuner matchade
på kommunkod (två DB-stavfel aliasade: Sölveborg→Sölvesborg, Sundvall→Sundsvall).

- Täckt kommunbefolkning: **4 826 169** av rikets **10 587 710**
- **Befolkningsviktad täckning: 45,6 %** — mot **51 %** oviktat (149/290).

Den viktade siffran är *lägre* än den oviktade → urvalet skevar mot **mindre**
kommuner. Största enskilda orsaken: **Stockholm (995 574 inv.) saknas** — står som
"avvakta" i 2024-loggen — liksom flera andra storstäder. Sanity-check: 441 671
kommunindivider mot ~890 000 kommunalt anställda i riket ≈ 50 %, i linje med ~46 %
befolkningstäckning.

Varning: befolkning är en proxy, inte exakt antal anställda. Exakt siffra kräver
SKR:s "antal anställda per kommun".
