// Delad copy som måste vara IDENTISK på flera ytor.
// METHOD_NOTE = rapportens metodnot. Samma text återanvänds som
// "Vår integritetsprincip" på /om-tjansten (enligt beställning DEL D).
export const METHOD_NOTE: string[] = [
  "Uppgifterna är inhämtade via offentlighetsprincipen från kommuner och " +
    "regioner och avser 2024 års löner. Lönerna är omräknade till " +
    "heltidsekvivalent månadslön. Statistik visas endast när minst 5 individer " +
    "har samma titel hos samma arbetsgivare respektive nationellt – " +
    "individuella löner publiceras aldrig.",
  "Median = mittenvärdet. Percentiler anger spridningen: 10:e percentilen är " +
    "den nivå som 10 % tjänar under, 90:e den nivå som 10 % tjänar över.",
];

// Täckningsrad – IDENTISK på yrkessidan och i lönerapporten.
// n_ft = poster med känd heltidslön (beräkningsunderlaget), n_raw = poster med
// månadslön satt (allt utlämnat). Visas alltid; vid full täckning kortas den.
export function coverageNote(nFt: number, nRaw: number): string {
  const fmt = (v: number) => v.toLocaleString("sv-SE");
  if (nFt >= nRaw) {
    return `Beräknat på samtliga ${fmt(nFt)} anställda.`;
  }
  return `Beräknat på ${fmt(nFt)} av ${fmt(nRaw)} anställda med uppgift om sysselsättningsgrad.`;
}
