import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "Offentliga löner", template: "%s | Offentliga löner" },
  description:
    "Lönestatistik för svensk offentlig sektor, insamlad via offentlighetsprincipen.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv" className={`${geist.className} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-white text-gray-900">
        <main className="flex-1">{children}</main>

        {/*
          Footer – obligatorisk enligt utgivningsbevis nr 2024-077.
          Databasens namn, tillhandahållare och ansvarig utgivare ska stå
          tydligt på varje sida. Får INTE tas bort utan ändrad teknisk
          beskrivning i beviset.
        */}
        <footer className="border-t border-gray-200 mt-16 py-6 px-4 text-xs text-gray-500">
          <div className="max-w-4xl mx-auto space-y-1">
            <p><strong>Offentliga löner, offentligaloner.se</strong></p>
            <p>
              Tillhandahållare och ansvarig utgivare:{" "}
              <strong>Patrik Larsson</strong>
            </p>
            <p>Utgivningsbevis nr 2024-077, giltigt t.o.m. 2034-10-28 (Mediemyndigheten)</p>
            <p className="pt-1 text-gray-400">
              Uppgifterna är inhämtade via offentlighetsprincipen och avser
              anställda i kommunal och regional sektor. Individdata publiceras
              aldrig — endast aggregat med minst 5 individer visas.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
