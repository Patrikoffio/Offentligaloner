import type { Metadata } from "next";
import { supabaseAdmin } from "@/lib/supabase";
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

export default async function OmTjansten() {
  const { count } = await supabaseAdmin
    .from("employers")
    .select("*", { count: "exact", head: true });
  const employerCount = (count ?? 156).toLocaleString("sv-SE");

  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-strong">
        Om tjänsten
      </p>
      <h1 className="font-serif text-4xl leading-tight text-gray-900 mt-1">
        Offentliga löner
      </h1>

      {/*
        ⚠️ PLATSHÅLLARTEXT – Patrik skriver om detta stycke före deploy.
        Nedan är beställningens textutkast, inlagt som utgångspunkt.
      */}
      <Section title="Varför Offentliga löner finns">
        <p>
          Offentliga löner startade med en enkel övertygelse: lönerna i offentlig
          sektor är redan offentliga – men i praktiken oåtkomliga för den som bäst
          behöver dem. Uppgifterna finns, utspridda hos kommuner och regioner, men
          den enskilda undersköterskan, läraren eller handläggaren har sällan tid
          eller verktyg att begära ut och tolka dem inför sin löneförhandling.
        </p>
        <p>
          Det ville jag ändra på. Sedan 2024 begär vi ut faktiska utbetalda löner
          enligt offentlighetsprincipen, kvalitetssäkrar dem och gör dem sökbara –
          för att arbetstagaren ska möta arbetsgivaren med samma kunskapsläge. Inga
          enkäter, inga uppskattningar. Och aldrig någonsin enskilda personers löner
          – bara mönstren, som hjälper dig se var du står.
        </p>
      </Section>

      <Section title="Vem står bakom">
        <div className="flex items-start gap-5">
          {/* Plats för foto (valfritt) – lägg en bild i /public och byt ut rutan. */}
          <div
            aria-hidden
            className="hidden sm:flex shrink-0 h-24 w-24 rounded-full bg-plate-blue border border-gray-200 items-center justify-center text-xs text-gray-400 text-center leading-tight"
          >
            Foto
            <br />
            (valfritt)
          </div>
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
          Underlaget hämtas in via offentlighetsprincipen: vi begär ut
          lönelistorna från kommuner och regioner, som är skyldiga att lämna ut
          dem. 2024 års insamling omfattar <strong>{employerCount}</strong>{" "}
          kommuner och regioner.
        </p>
        <p>
          Alla löner räknas om till heltidsekvivalent månadslön så att de går att
          jämföra rättvist, oavsett sysselsättningsgrad. Uppgifterna städas och
          kvalitetssäkras innan de publiceras – felaktiga och orimliga värden
          flaggas och utesluts. Nästa rikstäckande insamling inleds i augusti 2026.
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
