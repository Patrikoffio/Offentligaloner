# Granskningslista – preview före go-live (2026-07-22)

Sidbas: `http://localhost:3000`

## Exit-kriterium

Granskningen är **KLAR** – och steg 2 (promote) får köras – när alla rutor
nedan är ibockade och inga fynd kräver data- eller kodändring. Fynd som kräver
ändring: åtgärda, deploya ny preview, kör om detta skript, börja om på listan.
Ingen tredje kategori ("tar det sen") – då blir det aldrig go-live.

## A. Automatiska kontroller (kördes av skriptet)

- [x] ai_description fri från HTML-taggar (förväntat 0): 0
- [x] received_at satt på alla källdokument (förväntat 0 NULL): 0
- [x] publika nationella vyn innehåller inga n<5 (förväntat 0): 0
- [x] kön i salary_records endast K/M/NULL (förväntat 0 övriga): 0
- [x] tim/månad aldrig blandat (förväntat 0): 0

## B. Sidor att ögna

Per sida: rubrik/titel korrekt, statistik rimlig, källhänvisning med
utlämningsdatum, datering "2024 års insamling / augusti 2026", styckeindelad
beskrivning utan råa taggar, **ingen 2026-uppräkning synlig** (flaggan är AV).

### Störst underlag (layout under tryck, många arbetsgivarrader)

_Kontrollera tabellrendering, utfällbar källista, laddtid._

- [ ] Undersköterska — http://localhost:3000/yrken/underskoterska
- [ ] Förskollärare — http://localhost:3000/yrken/forskollarare
- [ ] Barnskötare — http://localhost:3000/yrken/barnskotare
- [ ] Sjuksköterska — http://localhost:3000/yrken/sjukskoterska
- [ ] Vårdbiträde — http://localhost:3000/yrken/vardbitrade

### Slumpade titlar med publicerbar data

_Normalfallet: statistik rimlig, styckeindelad beskrivning, källhänvisning + datum._

- [ ] Cafeteriabiträde — http://localhost:3000/yrken/cafeteriabitrade
- [ ] Yttre Befäl — http://localhost:3000/yrken/yttre-befal
- [ ] Undersköterska/Personlig Assistent — http://localhost:3000/yrken/underskoterskapersonlig-assistent
- [ ] Lärare (Vård- och Omsorgsämnen) — http://localhost:3000/yrken/larare-vard-och-omsorgsamnen
- [ ] Modersmålslärare/Handledare — http://localhost:3000/yrken/modersmalslararehandledare

### Informationssidor utan publicerbar data

_Kategoristatistik, similar_jobs-länkar, förklaringstext – inga tomma tabeller._

- [ ] Systemförvaltare/Samordnare — http://localhost:3000/yrken/systemforvaltaresamordnare
- [ ] Affärsjurist — http://localhost:3000/yrken/affarsjurist
- [ ] Lärare (Naturkunskap) — http://localhost:3000/yrken/larare-naturkunskap
- [ ] Sjukgymnast/Medicinskt Ansvarig för Rehabilitering (MAR) — http://localhost:3000/yrken/sjukgymnastmedicinskt-ansvarig-for-rehabilitering-mar
- [ ] Enhetschef (Barn och Ungdom/Ifo) — http://localhost:3000/yrken/enhetschef-barn-och-ungdomifo

### Titlar med n<5-arbetsgivarrader

_Raden ska visa antal MEN INGA lönevärden (granskningsändring 5)._

- [ ] Kommunsekreterare (Förste) — http://localhost:3000/yrken/kommunsekreterare-forste
- [ ] Senior Specialist Exploatering — http://localhost:3000/yrken/senior-specialist-exploatering
- [ ] Lärare (Grundskola) — http://localhost:3000/yrken/larare-grundskola
- [ ] Utbildningsstrateg — http://localhost:3000/yrken/utbildningsstrateg
- [ ] Utbildningsledare — http://localhost:3000/yrken/utbildningsledare

### Längst ai_description (städningen syns tydligast här)

_Flera stycken, ingen '<p>' eller annan råtagg, meta-description ren text (view-source)._

- [ ] Personlig Assistent/Undersköterska/Sköterska — http://localhost:3000/yrken/personlig-assistentunderskoterskaskoterska
- [ ] Lärare (Svenska/Religion) — http://localhost:3000/yrken/larare-svenskareligion
- [ ] Skopist/Sjuksköterska — http://localhost:3000/yrken/skopistsjukskoterska

### Nyligen flyttade kategorier (session 5/6-flyttar)

_Titeln ska ligga i rimlig kategori; brödsmula/kategorilänk stämmer._

- [ ] Stadsmiljöutvecklare — http://localhost:3000/yrken/stadsmiljoutvecklare
- [ ] Bemanningsutvecklare — http://localhost:3000/yrken/bemanningsutvecklare
- [ ] Eftermarknads- och Avtalssamordnare — http://localhost:3000/yrken/eftermarknads-och-avtalssamordnare
- [ ] Omvårdnadspersonal/Ekonomibiträde — http://localhost:3000/yrken/omvardnadspersonalekonomibitrade
- [ ] Ansvarig Digitala Kanaler — http://localhost:3000/yrken/ansvarig-digitala-kanaler
- [ ] Inköpsutvecklare — http://localhost:3000/yrken/inkopsutvecklare
- [ ] Ledare/Utvecklare — http://localhost:3000/yrken/ledareutvecklare
- [ ] Kundmottagare/Registrator — http://localhost:3000/yrken/kundmottagareregistrator

## C. Fasta kontroller (en gång, valfri sida om inget annat anges)

- [ ] Footer: databasens namn "Offentliga löner, offentligaloner.se",
      tillhandahållare, ansvarig utgivare Patrik Larsson, utgivningsbevis
      nr 2024-077 – syns på varje sida.
- [ ] Källhänvisning: aggregerad rad + utfällbar lista fungerar (matview 0006).
- [ ] Startsida + en kategorisida renderar och länkar rätt.
- [ ] Mobilbredd: yrkessida med bred tabell är läsbar.

## D. Redirects (förväntat: 301 + Location mot /yrken/...)

```bash
curl -sI http://localhost:3000/loner/rontgensjukskoterska | grep -Ei 'HTTP|location'
curl -sI http://localhost:3000/loner/boendekoordinator | grep -Ei 'HTTP|location'
curl -sI http://localhost:3000/loner/sprakstodjare | grep -Ei 'HTTP|location'
# plus minst en retirerad numrerad oktober-slug ur next.config:
# curl -sI http://localhost:3000/loner/<numrerad-slug> | grep -Ei 'HTTP|location'
```
