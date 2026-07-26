import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Integritetspolicy",
  description:
    "Så behandlar Offentliga löner personuppgifter vid köp av lönerapport – vilka uppgifter, ändamål, rättslig grund, lagringstid och dina rättigheter. Utgivningsbeviset för den publicistiska databasen är en separat fråga.",
  alternates: { canonical: "/integritetspolicy" },
  openGraph: { url: "/integritetspolicy", title: "Integritetspolicy" },
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

export default function Integritetspolicy() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-strong">
        Integritet
      </p>
      <h1 className="font-serif text-4xl leading-tight text-gray-900 mt-1">
        Integritetspolicy
      </h1>
      <p className="mt-4 text-[15px] leading-relaxed text-gray-700 max-w-2xl">
        Den här policyn beskriver hur vi behandlar personuppgifter när du köper en
        lönerapport på offentligaloner.se. Den gäller alltså kunduppgifter i
        köpflödet – inte den publicerade lönedatabasen, se avsnittet{" "}
        <em>Utgivningsbeviset – en separat fråga</em> längst ned.
      </p>

      <Section title="Personuppgiftsansvarig">
        <p>
          Ansvarig för behandlingen av personuppgifter vid köp är{" "}
          <strong>Patrik Larsson</strong>.
        </p>
        <ul className="list-disc pl-5 space-y-1">
          <li>Organisationsnummer: 19890405-4676</li>
          <li>Postadress: Tunnerbohult Marieslätt, 333 92 Broaryd</li>
          <li>
            E-post:{" "}
            <a
              href="mailto:kontakt@offentligaloner.se"
              className="text-brand-mid hover:underline"
            >
              kontakt@offentligaloner.se
            </a>
          </li>
        </ul>
      </Section>

      <Section title="Vilka uppgifter vi behandlar">
        <ul className="list-disc pl-5 space-y-1">
          <li>
            <strong>E-postadress</strong> – som du anger i kassan, för att leverera
            rapporten och skicka kvitto/orderbekräftelse.
          </li>
          <li>
            <strong>Betaluppgifter</strong> – hanteras av vår betalleverantör
            Stripe. Vi tar aldrig emot eller lagrar ditt kortnummer; vi ser endast
            att en betalning genomförts och tillhörande orderreferens.
          </li>
          <li>
            <strong>Orderuppgifter</strong> – vilka yrken och arbetsgivare du valt,
            belopp och tidpunkt, samt en slumpad länk (token) till rapporten.
          </li>
          <li>
            <strong>Löneuppgift du själv anger</strong> – om du väljer att fylla i
            vad du tjänar i dag (eller vilken lön du siktar på) för att se din egen
            placering i rapporten. Uppgiften behandlas <strong>enbart i din
            webbläsare</strong> när rapporten genereras – den skickas aldrig till
            våra servrar och sparas inte i vår databas.
          </li>
        </ul>
      </Section>

      <Section title="Ändamål och rättslig grund">
        <ul className="list-disc pl-5 space-y-1">
          <li>
            <strong>Leverera rapporten och ge kundservice</strong> – rättslig grund:
            fullgörande av avtalet med dig (dataskyddsförordningen art. 6.1 b).
          </li>
          <li>
            <strong>Visa din egen placering i rapporten</strong> (om du anger en
            löneuppgift) – rättslig grund: fullgörande av avtalet med dig
            (art. 6.1 b). Uppgiften används bara när rapporten genereras och sparas
            inte efteråt.
          </li>
          <li>
            <strong>Bokföring och redovisning</strong> – rättslig grund: rättslig
            förpliktelse (art. 6.1 c), enligt bokföringslagen.
          </li>
          <li>
            <strong>Hantera reklamationer och återbetalningar</strong> – rättslig
            grund: fullgörande av avtal samt vårt berättigade intresse av att kunna
            styrka och hantera köp (art. 6.1 b och f).
          </li>
        </ul>
      </Section>

      <Section title="Lagringstid">
        <p>
          Länken till rapporten är giltig i tre månader, därefter kan rapporten inte
          längre hämtas. Uppgifter som utgör bokföringsunderlag sparas så länge
          bokföringslagen kräver – i normalfallet sju år efter räkenskapsårets slut.
          När uppgifterna inte längre behövs för dessa ändamål gallras de.
        </p>
      </Section>

      <Section title="Vem vi delar uppgifter med">
        <p>
          Vi säljer aldrig dina uppgifter. För att kunna leverera tjänsten anlitar
          vi personuppgiftsbiträden som behandlar uppgifter för vår räkning:
        </p>
        <ul className="list-disc pl-5 space-y-1">
          <li>
            <strong>Stripe</strong> – betalningshantering.
          </li>
          <li>
            <strong>Postmark</strong> – utskick av transaktionsmejl (bekräftelse och
            rapportlänk).
          </li>
          <li>
            <strong>Vercel / Supabase</strong> – drift och lagring (EU-region).
          </li>
        </ul>
        <p>
          Med samtliga dessa biträden finns personuppgiftsbiträdesavtal som
          reglerar behandlingen för vår räkning.
        </p>
      </Section>

      <Section title="Dina rättigheter">
        <p>
          Du har rätt att begära tillgång till dina uppgifter, rättelse, radering,
          begränsning av behandlingen och dataportabilitet, samt att invända mot
          behandling som grundas på berättigat intresse. Kontakta oss på{" "}
          <a
            href="mailto:kontakt@offentligaloner.se"
            className="text-brand-mid hover:underline"
          >
            kontakt@offentligaloner.se
          </a>{" "}
          så hjälper vi dig.
        </p>
        <p>
          Om du anser att vi behandlar dina personuppgifter felaktigt har du rätt
          att klaga till Integritetsskyddsmyndigheten (IMY),{" "}
          <a
            href="https://www.imy.se"
            className="text-brand-mid hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            imy.se
          </a>
          .
        </p>
      </Section>

      <Section title="Utgivningsbeviset – en separat fråga">
        <p>
          Den publicerade lönedatabasen ”Offentliga löner” omfattas av ett
          utgivningsbevis (nr 2024-077) från Mediemyndigheten och har därmed
          grundlagsskydd. Den publiceringen regleras av tryckfrihetsförordningen och
          yttrandefrihetsgrundlagen och styrs av verksamheten, inte av
          dataskyddsförordningen på samma sätt som vanlig personuppgiftsbehandling.
        </p>
        <p>
          Den behandling som beskrivs i den här policyn – uppgifterna du lämnar när
          du <em>köper</em> en rapport – är en helt separat fråga och regleras av
          dataskyddsförordningen på vanligt sätt. Frågor om den publicerade
          lönedatan (till exempel rättelse av en uppgift) hanteras enligt vad som
          framgår under{" "}
          <Link href="/om-tjansten" className="text-brand-mid hover:underline">
            Om tjänsten
          </Link>
          .
        </p>
      </Section>

      <Section title="Kontakt">
        <p>
          Frågor om hur vi behandlar dina personuppgifter?{" "}
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
