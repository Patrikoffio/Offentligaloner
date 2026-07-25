import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Köpvillkor",
  description:
    "Köpvillkor för lönerapporten på Offentliga löner – vad som levereras, leveranstid, pris och moms, ångerrätt, 30 dagars nöjd-kund-garanti och hur du begär återbetalning.",
  alternates: { canonical: "/kopvillkor" },
  openGraph: { url: "/kopvillkor", title: "Köpvillkor" },
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

export default function Kopvillkor() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-12">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent-strong">
        Villkor
      </p>
      <h1 className="font-serif text-4xl leading-tight text-gray-900 mt-1">
        Köpvillkor
      </h1>
      <p className="mt-4 text-[15px] leading-relaxed text-gray-700 max-w-2xl">
        Dessa villkor gäller när du köper en lönerapport på offentligaloner.se.
        Läs dem tillsammans med vår{" "}
        <Link href="/integritetspolicy" className="text-brand-mid hover:underline">
          integritetspolicy
        </Link>
        .
      </p>

      <Section title="Vem du handlar av">
        <p>
          Tjänsten tillhandahålls av <strong>Patrik Larsson</strong>.
        </p>
        {/* TODO: fyll i säljarens företagsform, organisationsnummer och postadress. */}
        <ul className="list-disc pl-5 space-y-1">
          <li>Organisationsnummer: TODO – fyll i organisationsnummer</li>
          <li>Postadress: TODO – fyll i postadress</li>
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

      <Section title="Vad du får">
        <p>
          Produkten är en <strong>lönerapport</strong> i digitalt format,
          anpassad för att läsas i webbläsare och sparas som PDF/skrivas ut. Varje
          rapport omfattar upp till 5 yrken och upp till 5 valda kommuner eller
          regioner. Per yrke visas nationell lönespridning som referens samt
          statistik för de arbetsgivare du valt.
        </p>
        <p>
          All statistik bygger på aggregerade uppgifter där minst 5 individer
          ingår. Rapporten innehåller aldrig individuella löneuppgifter. Underlaget
          avser 2024 års insamling och är kopplat till källa och utlämningsdatum.
        </p>
        <p>
          Rapporten nås via en personlig länk och är{" "}
          <strong>giltig i tre månader</strong> från köpet. Efter det upphör
          länken att fungera.
        </p>
      </Section>

      <Section title="Pris och moms">
        <p>
          Rapporten kostar <strong>99 kr inkl. moms</strong>. Priset anges i
          svenska kronor och är ett engångsköp – ingen prenumeration.
        </p>
      </Section>

      <Section title="Betalning">
        <p>
          Betalning sker i kassan via Stripe, med kort eller Klarna. Vi lagrar
          aldrig dina kortuppgifter – de hanteras direkt av Stripe. Kvitto och en
          bekräftelse med länk till rapporten skickas till den e-postadress du
          anger i kassan.
        </p>
      </Section>

      <Section title="Leverans">
        <p>
          Rapporten är en digital tjänst som levereras{" "}
          <strong>direkt efter genomförd betalning</strong>. Så snart betalningen
          bekräftats visas en länk till rapporten och samma länk skickas till din
          e-post.
        </p>
        <p>
          Vid kortbetalning sker detta normalt inom några minuter. Väljer du
          Klarna kan bekräftelsen dröja – rapporten skickas så snart Klarna
          bekräftat betalningen.
        </p>
      </Section>

      <Section title="Ångerrätt">
        <p>
          Enligt lagen om distansavtal och avtal utanför affärslokaler har du som
          konsument normalt 14 dagars ångerrätt. För digitalt innehåll som levereras
          omedelbart upphör dock ångerrätten när leveransen påbörjats, om du
          uttryckligen samtyckt till det och bekräftat att du därmed förlorar
          ångerrätten.
        </p>
        <p>
          I kassan får du därför kryssa i ett uttryckligt samtycke till omedelbar
          leverans. När du gör det, och rapporten levereras, upphör ångerrätten.
          Utan detta samtycke kan köpet inte genomföras.
        </p>
      </Section>

      <Section title="30 dagars nöjd-kund-garanti">
        <p>
          Även om ångerrätten upphör vid leverans lämnar vi frivilligt en{" "}
          <strong>nöjd-kund-garanti i 30 dagar</strong>. Är du av någon anledning
          inte nöjd med rapporten kan du kontakta oss inom 30 dagar från köpet och
          få pengarna tillbaka. Du behöver inte ange något skäl.
        </p>
      </Section>

      <Section title="Reklamation">
        <p>
          Om tjänsten är felaktig – till exempel om länken inte fungerar eller
          rapporten inte innehåller det som beställdes – ber vi dig kontakta oss så
          snart du upptäckt felet. Vi rättar felet eller återbetalar köpet. Din rätt
          att reklamera fel enligt konsumentlagstiftningen påverkas inte av
          nöjd-kund-garantin ovan.
        </p>
      </Section>

      <Section title="Så begär du återbetalning">
        <p>
          Mejla{" "}
          <a
            href="mailto:kontakt@offentligaloner.se"
            className="text-brand-mid hover:underline"
          >
            kontakt@offentligaloner.se
          </a>{" "}
          från, eller med uppgift om, den e-postadress du använde vid köpet.
          Återbetalning görs till samma betalmedel via Stripe inom 5 arbetsdagar.
        </p>
      </Section>

      <Section title="Om vi inte kommer överens">
        <p>
          Skulle det uppstå en tvist som vi inte kan lösa tillsammans kan du som
          konsument vända dig till Allmänna reklamationsnämnden (ARN), som prövar
          ärendet kostnadsfritt. Vi följer ARN:s rekommendationer.
        </p>
        <p>
          Allmänna reklamationsnämnden, Box 174, 101 23 Stockholm –{" "}
          <a
            href="https://www.arn.se"
            className="text-brand-mid hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            arn.se
          </a>
          .
        </p>
      </Section>

      <Section title="Kontakt">
        <p>
          Frågor om ett köp eller dessa villkor?{" "}
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
