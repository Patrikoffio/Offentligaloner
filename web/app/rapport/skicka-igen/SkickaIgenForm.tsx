"use client";

import { useState } from "react";

export default function SkickaIgenForm() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    try {
      const res = await fetch("/api/report/resend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = (await res.json()) as { message?: string };
      if (res.status === 429) {
        setState("error");
        setMessage(data.message ?? "För många försök. Försök igen om en stund.");
        return;
      }
      setState("done");
      setMessage(
        data.message ??
          "Om det finns giltiga rapporter kopplade till adressen skickar vi länkarna dit.",
      );
    } catch {
      setState("error");
      setMessage("Något gick fel. Försök igen om en stund.");
    }
  }

  if (state === "done") {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-5 text-sm text-green-900">
        {message}
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          E-postadress
        </label>
        <input
          id="email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="din@epost.se"
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30"
        />
      </div>
      {state === "error" && (
        <p className="text-sm text-red-600">{message}</p>
      )}
      <button
        type="submit"
        disabled={state === "sending"}
        className="bg-brand text-white text-sm px-4 py-2 rounded-lg hover:opacity-90 disabled:opacity-50"
      >
        {state === "sending" ? "Skickar…" : "Skicka mina rapportlänkar"}
      </button>
    </form>
  );
}
