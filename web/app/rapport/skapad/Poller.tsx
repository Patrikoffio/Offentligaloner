"use client";

import { useEffect, useState } from "react";

// Pollar report-status en kort stund (Klarna kan bekräfta med fördröjning).
// Visar länken direkt när betalningen är bekräftad; annars faller sidan tillbaka
// på "mejlas när betalningen bekräftats".
export default function Poller({ sessionId }: { sessionId: string }) {
  const [token, setToken] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let active = true;
    let tries = 0;
    const maxTries = 20; // ~60 s (3 s intervall)

    async function tick() {
      if (!active) return;
      tries += 1;
      try {
        const res = await fetch(
          `/api/report-status?session_id=${encodeURIComponent(sessionId)}`,
          { cache: "no-store" },
        );
        const data = (await res.json()) as { ready?: boolean; token?: string };
        if (active && data.ready && data.token) {
          setToken(data.token);
          return; // klar – sluta polla
        }
      } catch {
        /* nätfel – försök igen */
      }
      if (active && tries < maxTries) {
        setTimeout(tick, 3000);
      } else if (active) {
        setDone(true);
      }
    }

    tick();
    return () => {
      active = false;
    };
  }, [sessionId]);

  if (token) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-5">
        <p className="font-medium text-green-900 mb-3">Din rapport är klar!</p>
        <a
          href={`/rapport/${token}`}
          className="inline-block bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90"
        >
          Öppna lönerapporten
        </a>
        <p className="text-xs text-green-800 mt-3">
          Vi har även mejlat länken till dig. Spara den – den är giltig i tre månader.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-plate-blue border border-brand-light rounded-lg p-5">
      <p className="font-medium text-blue-900 mb-2">
        {done ? "Rapporten mejlas när betalningen bekräftats" : "Bekräftar din betalning…"}
      </p>
      <p className="text-sm text-blue-800">
        {done
          ? "Betalningen kan ta en stund att bekräftas (särskilt med Klarna). Så fort " +
            "den är klar mejlar vi rapportlänken till dig. Du kan stänga den här sidan."
          : "Ett ögonblick – vi väntar in bekräftelsen från betalleverantören."}
      </p>
      <p className="text-xs text-brand mt-3">
        Fick du inget mejl?{" "}
        <a href="/rapport/skicka-igen" className="underline">
          Skicka länken igen
        </a>
        .
      </p>
    </div>
  );
}
