// Delad copy som måste vara IDENTISK på flera ytor.
// METHOD_NOTE = rapportens metodnot. Samma text återanvänds som
// "Vår integritetsprincip" på /om-tjansten (enligt beställning DEL D).
export const METHOD_NOTE: string[] = [
  "Uppgifterna är inhämtade via offentlighetsprincipen från kommuner och " +
    "regioner och avser 2024 års löner. Lönerna avser överenskommen månadslön " +
    "vid heltid. Statistik visas endast när minst 5 individer " +
    "har samma titel hos samma arbetsgivare respektive nationellt – " +
    "individuella löner publiceras aldrig.",
  "Median = mittenvärdet. Percentiler anger spridningen: 10:e percentilen är " +
    "den nivå som 10 % tjänar under, 90:e den nivå som 10 % tjänar över.",
];

// Täckningsrad – IDENTISK på yrkessidan och i lönerapporten.
// n = antal månadsavlönade i beräkningen; n_hourly = timavlönade som INTE ingår
// (de saknar jämförbar månadslön). Andra meningen utelämnas när n_hourly = 0.
export function coverageNote(n: number, nHourly: number): string {
  const fmt = (v: number) => v.toLocaleString("sv-SE");
  const base = `Beräknat på ${fmt(n)} månadsavlönade anställda.`;
  return nHourly > 0 ? `${base} ${fmt(nHourly)} timavlönade ingår inte.` : base;
}
