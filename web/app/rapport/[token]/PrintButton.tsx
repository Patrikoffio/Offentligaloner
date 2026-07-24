"use client";

// Skriv ut / spara som PDF. Döljs vid utskrift (print:hidden på wrappern).
export default function PrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="text-sm bg-brand text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
    >
      Skriv ut / spara som PDF
    </button>
  );
}
