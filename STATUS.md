# offentligaloner.se — läge 26 juli 2026

## Stack
Next.js 16 på Vercel · Supabase · Stripe Checkout · Postmark
Migrerad från Django/Hetzner (65.21.55.235) den 24 juli 2026.
Hetzner kvar som fallskärm, ej uppsagd.

## Aldrig röra
- Redirect `/loner/:slug → /yrken/:slug` i next.config. Bär hela den
  organiska trafiken. Google har indexerat v1:s /loner/-URL:er.
- MX- och TXT-poster i Loopias DNS (mejl + Postmark DKIM).

---

## Verifierat 26 juli — med bevis

| Fråga | Svar | Bevis |
|---|---|---|
| www-dubbletter | Löst | `curl -sI` ger 308 → rot |
| Hemligheter i git | Inga läckta | `git ls-files \| grep` = bara platshållare |
| Stripe-webhook | Fungerar | endpoint aktiv, 0 % fel, `checkout.session.completed` ikryssad |
| Kvittomejl | Levererat 16:35:33 | Postmark Activity, "Delivered" |
| Kvittot som saknades | Aldrig byggt | Enda mejlet är leveransbekräftelse, inget kvitto |
| Tröskelns effekt | Bekräftad | Ekolog: 10 arbetsgivare lämnade uppgifter, 1 klarade n≥5 |

## Avfärdade hypoteser
- Dubbelindexering www/icke-www → gamla URL-prefix-egendomar i Search
  Console, inte verklig dubbelindexering. Läs domänegendomen.
- Trasig webhook → Stripe-mejlet om fel gällde **testläge** mot Djangos
  gamla sökväg `/webhooks/stripe/`. Live-endpointen är frisk.
- Trasig kvittokedja → hela kedjan fungerar, funktionen finns inte.

## Ej mätt — det här är luckorna
- **Konverteringsgrad.** Ingen siffra finns. 36 221 klick/12 mån mot
  99 kr-produkt. Utan denna siffra går ingen prioritering att göra.
- **5xx-triagen.** 590 URL:er, ej körd. Skript: `pipeline/triage_5xx.py`
  (stdlib, kräver ingen pip). Indata: Search Console → Indexering →
  Sidor → "Serverfel (5xx)" → Exportera.
  Hypotes: historiska. Fel började 23 juli 17:37 UTC, dagen före DNS-bytet.
- **Tröskeln över alla 2 151 AID-titlar.** Endast Ekolog stickprovad.
- **CTR.** ~2 M visningar, 1,8 % CTR. Desktop 1,0 % är onormalt lågt.

---

## Arbetslista

### A — produktfel i det kunden betalar för
1. ✅ `"1:a högsta medianlönen av 1 arbetsgivare"` — villkora bort när
   antal arbetsgivare = 1
2. ✅ Metodtexten säger "samtliga 10 arbetsgivare", tabellen säger 1.
   Två nämnare i samma dokument utan förklaring.
   (kolumnrubrik "Antal" → "Anställda" i rapport + yrkessida)
3. Percentildiagrammet saknar markör för användarens egen lön.
   Den finns bara som brödtext. Det är hela individualiseringen.
4. Falsk precision: vid n=19 avrunda p10/p90 till närmaste 500 kr,
   eller visa bara p25–p75.
5. ✅ Loggan i rapportkomponenten är en tom hexagon — egen hårdkodad SVG
   som aldrig uppdaterades vid v1-bytet. Använd headerns komponent.
   (Logo.tsx = inline hela v1-loggan via logo-svg.ts; enda källan)
6. ✅ Header spränger mobilen under 400 px.
   (symbol-only < sm, full logga ≥ sm; header-överflöd verifierat = 0.
   OBS: kvarstående sid-överflöd < 385 px kommer från "Vanligaste
   yrkena"-listan, INTE headern — ej ännu åtgärdat, se not.)
7. Percentilstaplarna på yrken/[slug]/page.tsx utgår från noll, så
   p10 och p90 blir nästan lika långa på mobil. Fixen är att låta
   skalan börja strax under p10 i stället för på noll. Separat från
   punkt 3, som gäller DistributionBand.tsx i rapporten.
8. ✅ "Vanligaste yrkena"-listan på startsidan spränger mobilen < 385 px:
   raden är flex med en shrink-0-spann ("median … · … anställda") som
   inte krymper → horisontell scroll (65 px vid 320, 25 px vid 360).
   INTE headern (verifierat 0). Fix: stapla på mobil (flex-col < sm),
   radbrytning i stället för scroll. Mätt grön (scrollWidth = viewport
   vid 320/360/390).
9. Nyckeltalskorten på startsidan: stora talen (t.ex. "534 293",
   tnum text-2xl i grid-cols-3) är bredare än sin cell < ~360 px och
   tänjer sig något utanför plattan. INNESLUTET – ingen scroll
   (scrollWidth = viewport). Ej brådskande – vänta till samlad mobilrunda.

### B — mätningar
7. Konverteringsfunnel: yrkessida → checkout → betalning
8. Tröskelfördelning över alla titlar, korsad mot topp-200 sökfrågor
9. 5xx-triagen

### C — intäkt
10. Titeltaggar med siffror: "Psykologassistent: medianlön 39 500 kr (2025)"
    2 M visningar × +0,7 pp CTR ≈ 14 000 extra klick/år
11. Stripe: slå på kundmejl "Lyckade betalningar" + företagsinformation
12. Momshantering i kvittot — stäm av med bokföring

### D — städning
13. Två repos innehåller appen. Kolla Vercel → Settings → Git,
    behåll ett, arkivera det andra.
14. Radera inaktiverad Stripe-endpoint mot `/webhooks/stripe/`
15. Byt webhook-URL från `offentligaloner.vercel.app` till `offentligaloner.se`
16. Postmark gratisnivå: 100 mejl/månad. Slår i taket vid ~100 sälj.
17. `npm config set prefix ~/.npm-global` för npm-rättighetsfelet

---

## Regler för Claude Code i det här projektet
- Ingen deploy, commit eller push utan uttryckligt godkännande
- Visa diff före ändring
- `python3`, inte `python` (macOS)
- Mät före bygg: varje punkt får en siffra som motiverar den
