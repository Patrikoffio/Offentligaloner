import type { Metadata } from "next";
import Image from "next/image";
import { METHOD_NOTE } from "@/lib/copy";

export const metadata: Metadata = {
  title: "Om tjänsten",
  description:
    "Om Offentliga löner – varför tjänsten finns, vem som står bakom och hur lönedatan samlas in enligt offentlighetsprincipen.",
  alternates: { canonical: "/om-tjansten" },
  openGraph: { url: "/om-tjansten", title: "Om tjänsten" },
};

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-10">
      <h2 className="font-serif text-2xl text-gray-900 mb-3">{title}</h2>
      <div className="space-y-3 text-[15px] leading-relaxed text-gray-700 max-w-2xl">
        {children}
      </div>
    </section>
  );
}

export default function OmTjansten() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-strong">
        Om tjänsten
      </p>
      <h1 className="font-serif text-4xl leading-tight text-gray-900 mt-1">
        Offentliga löner
      </h1>

      <Section title="Varför Offentliga löner finns">
        <p>
          Lönerna i offentlig sektor är offentliga handlingar. I praktiken är de
          ändå svåra att komma åt: uppgifterna finns utspridda hos varje enskild
          kommun, region och myndighet, i olika format, och kräver att någon begär
          ut dem och sammanställer dem.
        </p>
        <p>
          Det gör att parterna i ett lönesamtal sällan har samma bild.
          Arbetsgivaren har lönestatistik, budgetramar och kännedom om hela sin
          personalstyrka. Den anställde har oftast rykten, ett par kollegor att
          jämföra med och en känsla av att ligga rätt eller fel. Det är ingen bra
          grund för ett samtal som ska handla om prestation och ansvar.
        </p>
        <p>
          Offentligalöner finns för att jämna ut den skillnaden. Vi har begärt ut
          lönelistor från 156 kommuner och regioner och sammanställt dem till en
          enhetlig databas: 534 293 löneuppgifter från 2024 års insamling,
          omräknade till heltidsekvivalent lön så att deltid inte snedvrider
          jämförelsen. För 2 151 yrkestitlar finns tillräckligt underlag för att
          redovisa statistik som går att luta sig mot. För yrken där underlaget är
          för litet för att redovisa löner utan att enskilda personer kan
          identifieras visar vi i stället vad vi vet om yrket och var det
          förekommer.
        </p>
        <p>
          <strong>För dig som är anställd</strong> betyder det att du kan gå in i
          lönesamtalet med siffror i stället för antaganden – och veta både var du
          står och vad som är rimligt att fråga efter.
        </p>
        <p>
          <strong>För dig som är arbetsgivare</strong> betyder det samma sak från
          andra hållet: ett oberoende jämförelseunderlag vid rekrytering,
          lönekartläggning och den egna lönebildningen, särskilt om den egna
          organisationen är för liten för att ge meningsfull statistik.
        </p>
        <p>
          Vi tar inte ställning i enskilda löneförhandlingar och gör inga
          rekommendationer om vad någon bör tjäna. Vi redovisar vad som faktiskt
          betalas, varifrån uppgifterna kommer och när de samlades in. Vad man gör
          med den kunskapen är upp till den som läser.
        </p>
      </Section>

      <Section title="Vem står bakom">
        <div className="flex items-start gap-5">
          <Image
            src="/patrik.jpg"
            alt="Patrik Larsson, ansvarig utgivare"
            width={96}
            height={96}
            className="block shrink-0 h-20 w-20 sm:h-24 sm:w-24 rounded-full object-cover border border-gray-200"
          />
          <div className="space-y-3">
            <p>
              Tjänsten drivs av <strong>Patrik Larsson</strong>, som är både
              tillhandahållare och ansvarig utgivare för databasen.
            </p>
            <p>
              Offentliga löner publiceras under utgivningsbevis nr 2024-077 från
              Mediemyndigheten. Utgivningsbeviset innebär att verksamheten – inte
              användarna – ansvarar för och bestämmer över innehållet, och att
              publiceringen omfattas av grundlagsskydd.
            </p>
          </div>
        </div>
      </Section>

      <Section title="Så samlas datan in">
        <p>
          Löner i offentlig sektor är offentliga handlingar. Vi begär ut dem direkt
          från arbetsgivarna – 156 kommuner och regioner lämnade ut sina
          lönelistor för 2024 års insamling. Uppgifterna kommer in i vitt skilda
          format och sammanställs hos oss till en enhetlig databas, där lönerna
          räknas om till heltidsekvivalent nivå och yrkestitlar grupperas så att
          samma yrke blir jämförbart mellan arbetsgivare. Varje publicerad siffra
          är kopplad till sitt utlämningsdatum och sin källa.
        </p>
      </Section>

      <Section title="Vår integritetsprincip">
        {METHOD_NOTE.map((para, i) => (
          <p key={i}>{para}</p>
        ))}
      </Section>

      <Section title="Kontakt">
        <p>
          Frågor, rättelser eller önskemål om datauttag?{" "}
          <a
            href="mailto:kontakt@offentligaloner.se"
            className="text-brand-mid hover:underline"
          >
            kontakt@offentligaloner.se
          </a>
        </p>
      </Section>
    </div>
  );
}
