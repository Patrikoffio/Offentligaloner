# Intagsrutin – insamling 2026

Rutin för hur inkommande lönefiler tas emot, läggs, namnges och loggas.
Gäller 2026 års insamling (regioner + kommuner).

## 1. Var filer läggs

Alla råfiler under `data/raw/2026/`, en undermapp per **avsändare**:

```
data/raw/2026/
  regioner/
    vastmanland/
    <region>/
  kommuner/
    <kommun>/
```

- Avsändarmappen: **gemener, å/ä→a, ö→o, mellanslag/övrigt → bindestreck**
  (samma regel som slugs för nya titlar, `pipeline/slugs.py:slugify_new`).
  Ex: `Region Västmanland` → `vastmanland/`, `Västerås stad` → `vasteras/`.
- Region under `regioner/`, kommun/kommunalförbund/bolag/myndighet under
  respektive gren (lägg till fler grenar vid behov, samma namnregel).

## 2. Hur filer namnges

```
lonestatistik-<avsändare>-<ÅÅÅÅ-MM>.xlsx
```

- `<avsändare>` = samma slug som mappnamnet.
- `<ÅÅÅÅ-MM>` = perioden filen **avser**. Härleds ur avsändarens filnamn,
  som ofta är inkonsekvent (publiceringsdatum, årtal+månadsnamn, stavfel).
  Ex från Västmanland: `...-2022-december.xlsx` → `2022-12`,
  `...-20260703.xlsx` → `2026-07`, `...-2026-05-05-ny.xlsx` → `2026-05`.
- En fil per period och avsändare. Kolliderar två källfiler på samma period,
  behåll originalfilnamnet med suffix och notera i loggen.
- Behåll **aldrig** avsändarens råa filnamn som slutnamn – normalisera alltid.

## 3. Vad som loggas

Varje mottagen fil får **en rad** i `docs/kampanj/leveranslogg.csv`
(committas – innehåller bara metadata, aldrig lönedata). Kolumner:

| Kolumn | Innehåll |
|---|---|
| `arbetsgivare` | Fullt namn, t.ex. `Region Västmanland` |
| `typ` | `region` / `kommun` / `kommunalforbund` / `bolag` / `myndighet` |
| `mottaget_datum` | ÅÅÅÅ-MM-DD när filen kom in/hämtades |
| `diarienummer` | Vid begäran enligt offentlighetsprincipen; tomt för öppen data |
| `filnamn` | Det normaliserade namnet på disk (se §2) |
| `format` | `xlsx` / `csv` / `pdf` … |
| `avser_period` | ÅÅÅÅ-MM som filen avser |
| `granskad` | `ja` / `nej` – rimlighetsgranskad (radantal, medellön, sentineler) |
| `importerad` | `ja` / `nej` – inläst i v2 via parser |
| `anteckning` | Källa, taxa, avslag, e-legitimationskrav, avvikelser m.m. |

Logga även **processverklighet** (taxa, avslag, vägrar digitalt, krångel) i
`anteckning` – det är affärskritisk insamlingskunskap, inte bara filspårning.

## 4. Hård regel: råfiler committas ALDRIG

`data/` är gitignorerad (`.gitignore` rad 2). Råfiler kan innehålla
personuppgifter och **git glömmer aldrig** – en gång committat, kvar för alltid.
Kontrollera före varje commit att inget under `data/` är steg­at:

```
git status --short        # inga data/-rader
git check-ignore data/raw/2026/…   # ska svara IGNORERAD
```

Endast metadata (den här filen + `leveranslogg.csv`) hör hemma i git.

## 5. Efter intag (nästa steg, utanför denna rutin)

Parser per avsändarformat (`pipeline/parsers/_template.py`), fixture-test,
provimport lokalt, rimlighetsgranskning av antal + medellön **före** produktion.
Städsteget måste fånga personnamn i könsfält och sentineler – se projektreglerna.
