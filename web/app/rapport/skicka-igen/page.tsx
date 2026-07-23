import type { Metadata } from "next";
import SkickaIgenForm from "./SkickaIgenForm";

export const metadata: Metadata = {
  title: "Skicka rapportlänk igen",
  robots: { index: false, follow: false },
};

export default function SkickaIgenSida() {
  return (
    <div className="max-w-md mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold mb-3">Skicka rapportlänken igen</h1>
      <p className="text-gray-600 text-sm mb-6">
        Ange e-postadressen du använde vid köpet, så mejlar vi dina giltiga
        rapportlänkar dit igen. Av säkerhetsskäl bekräftar vi aldrig om en adress
        har köpt en rapport.
      </p>
      <SkickaIgenForm />
    </div>
  );
}
