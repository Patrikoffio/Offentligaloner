"use client";

// Skriv ut / spara som PDF. Döljs vid utskrift (print:hidden).
export default function PrintButton() {
  return (
    <button
      onClick={() => window.print()}
      className="print:hidden text-sm bg-gray-900 text-white px-4 py-2 rounded hover:bg-gray-700"
    >
      Skriv ut / spara som PDF
    </button>
  );
}
