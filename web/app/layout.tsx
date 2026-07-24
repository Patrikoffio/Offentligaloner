import type { Metadata } from "next";
import { Geist, Source_Serif_4 } from "next/font/google";
import Link from "next/link";
import { siteUrl } from "@/lib/site";
import SiteHeader from "@/components/SiteHeader";
import PaymentMarks from "@/components/PaymentMarks";
import "./globals.css";

// Sans (UI/brödtext) + serif (rubriker i hero/rapport, positionsnot i kursiv).
// Exponeras som CSS-variabler och mappas till font-sans/font-serif i globals.css.
const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  display: "swap",
  style: ["normal", "italic"],
});

// metadataBase gör relativa canonical/og:url absoluta mot kanonisk bas (utan
// www). Sätt INGEN canonical eller og:url här – det skulle ärvas av alla sidor;
// de sätts per sida (startsida + yrkessida). Här bara sajtgemensamma og-fält.
export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: "Offentliga löner", template: "%s | Offentliga löner" },
  description:
    "Lönestatistik för svensk offentlig sektor, insamlad via offentlighetsprincipen.",
  openGraph: {
    type: "website",
    siteName: "Offentliga löner",
    locale: "sv_SE",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="sv"
      className={`${geist.variable} ${sourceSerif.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-gray-900">
        <SiteHeader />
        <main className="flex-1">{children}</main>

        {/*
          Footer – obligatorisk enligt utgivningsbevis nr 2024-077.
          Databasens namn, tillhandahållare och ansvarig utgivare ska stå
          tydligt på varje sida. Får INTE tas bort utan ändrad teknisk
          beskrivning i beviset. Döljs vid utskrift (print:hidden) – den
          utskrivna lönerapporten bär sin egen sidfot med samma uppgifter.
        */}
        <footer className="print:hidden border-t border-gray-200 mt-16 py-8 px-4 text-xs text-gray-500">
          <div className="max-w-4xl mx-auto space-y-4">
            <PaymentMarks />
            <div className="space-y-1">
              <p>
                <strong className="text-gray-700">
                  Offentliga löner, offentligaloner.se
                </strong>
              </p>
              <p>
                Tillhandahållare och ansvarig utgivare:{" "}
                <strong>Patrik Larsson</strong>
              </p>
              <p>
                Utgivningsbevis nr 2024-077, giltigt t.o.m. 2034-10-28
                (Mediemyndigheten)
              </p>
              <p className="pt-1 text-gray-400 max-w-2xl">
                Uppgifterna är inhämtade via offentlighetsprincipen och avser
                anställda i kommunal och regional sektor. Individdata publiceras
                aldrig — endast aggregat med minst 5 individer visas.
              </p>
              <p className="pt-1">
                <Link href="/om-tjansten" className="text-brand-mid hover:underline">
                  Om tjänsten
                </Link>{" "}
                ·{" "}
                <a
                  href="mailto:kontakt@offentligaloner.se"
                  className="text-brand-mid hover:underline"
                >
                  kontakt@offentligaloner.se
                </a>
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
