// Momsspecifikation för orderbekräftelsen (kvittomejl + ev. rapportsida).
// Priset anges INKL. moms (digital tjänst, Sverige). Ändra satsen HÄR – ett ställe.
export const MOMSSATS = 0.25;

// Svenskt belopp med två decimaler och decimalkomma, t.ex. "79,20".
function belopp(n: number): string {
  return n.toLocaleString("sv-SE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export interface Momsspec {
  exklMoms: string; // netto (formaterat)
  moms: string; // momsbelopp (formaterat)
  brutto: string; // att betala (formaterat)
  satsProcent: number; // t.ex. 25
}

// amountSek = bruttopris inkl. moms (kr). Momsen deriveras baklänges och
// avrundas till öre; nettot beräknas som brutto − moms så att
// netto + moms === brutto exakt (inget öre försvinner i avrundningen).
export function momsspec(amountSek: number): Momsspec {
  const moms = Math.round(((amountSek * MOMSSATS) / (1 + MOMSSATS)) * 100) / 100;
  const exkl = amountSek - moms;
  return {
    exklMoms: belopp(exkl),
    moms: belopp(moms),
    brutto: belopp(amountSek),
    satsProcent: Math.round(MOMSSATS * 100),
  };
}
