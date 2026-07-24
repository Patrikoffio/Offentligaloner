import { CreditCard, ShieldCheck } from "lucide-react";

export interface PaymentLogo {
  src: string;
  alt: string;
}

// Betalningstrygghet under köpknappen. Textvarianten renderas alltid; finns
// officiella betalmärken i /public/payment/ läggs de i en rad ovanför (enhetlig
// optisk höjd ~24 px, 12 px mellanrum, ingen filter-/färgstyling). Vilka märken
// som finns avgörs server-side i lib/paymentLogos.ts – inga egna logotyper.
export function PaymentTrust({ logos = [] }: { logos?: PaymentLogo[] }) {
  return (
    <div className="mt-4 flex flex-col items-center gap-2 text-sm text-gray-600">
      {logos.length > 0 && (
        <div className="flex items-center gap-3">
          {logos.map((l) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={l.alt} src={l.src} alt={l.alt} className="h-6 w-auto" />
          ))}
        </div>
      )}
      <div className="flex items-center gap-2">
        <CreditCard className="h-4 w-4" aria-hidden="true" />
        <span>Kort&nbsp;· Klarna&nbsp;· Apple&nbsp;Pay&nbsp;· Google&nbsp;Pay</span>
      </div>
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
        <span>
          Betalningen hanteras av Stripe. Vi lagrar aldrig dina kortuppgifter.
        </span>
      </div>
    </div>
  );
}
