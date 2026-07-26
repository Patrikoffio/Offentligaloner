// Intern förhandsvisning av spridningsbandets egna-lön-markör (punkt A3).
// noindex – inte länkad, endast för granskning. Kan tas bort efteråt.
import type { Metadata } from "next";
import BandPreview from "./BandPreview";

export const metadata: Metadata = {
  title: "Förhandsvisning – spridningsband",
  robots: { index: false, follow: false },
};

export default function ForhandsvisningSida() {
  return <BandPreview />;
}
