import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Köp avbrutet",
  robots: { index: false, follow: false },
};

export default function AvbrutenSida() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-16">
      <h1 className="text-2xl font-bold mb-3">Köpet avbröts</h1>
      <p className="text-gray-600 mb-6">
        Ingen betalning genomfördes. Du kan gå tillbaka och beställa rapporten igen
        när du vill.
      </p>
      <a
        href="/"
        className="inline-block bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
      >
        Till startsidan
      </a>
    </div>
  );
}
