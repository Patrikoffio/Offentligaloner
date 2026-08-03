// Postmark-utskick (ENDAST server-side) via HTTP-API – ingen extra dependency.
// Samma Postmark-konto som gamla sajten; avsändare no-reply@offentligaloner.se.
// POSTMARK_SERVER_TOKEN får aldrig NEXT_PUBLIC-prefix.
import { reportUrl, siteUrl } from "./site";
import { momsspec } from "./moms";

const POSTMARK_URL = "https://api.postmarkapp.com/email";

function fromAddress(): string {
  return process.env.POSTMARK_FROM ?? "no-reply@offentligaloner.se";
}

// Svenskt datum (utan tid) för utgångsdatum i mejlet.
function formatDate(d: Date): string {
  return d.toLocaleDateString("sv-SE", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

interface SendResult {
  ok: boolean;
  error?: string;
}

async function postmarkSend(opts: {
  to: string;
  subject: string;
  htmlBody: string;
  textBody: string;
}): Promise<SendResult> {
  const token = process.env.POSTMARK_SERVER_TOKEN;
  if (!token) return { ok: false, error: "POSTMARK_SERVER_TOKEN saknas" };

  try {
    const res = await fetch(POSTMARK_URL, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": token,
      },
      body: JSON.stringify({
        From: fromAddress(),
        To: opts.to,
        Subject: opts.subject,
        HtmlBody: opts.htmlBody,
        TextBody: opts.textBody,
        MessageStream: "outbound",
      }),
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      return { ok: false, error: `Postmark ${res.status}: ${detail}` };
    }
    return { ok: true };
  } catch (e) {
    return { ok: false, error: (e as Error).message };
  }
}

// Köpbekräftelse: token-länk till rapporten + utgångsdatum (3 mån).
export async function sendReportEmail(opts: {
  to: string;
  token: string;
  expiresAt: Date;
  orderRef: string;
  purchaseDate: Date;
  amountSek: number; // bruttopris inkl. moms – momsspecen räknas fram från detta
}): Promise<SendResult> {
  const url = reportUrl(opts.token);
  const expiry = formatDate(opts.expiresAt);
  const purchased = formatDate(opts.purchaseDate);
  const kopvillkorUrl = `${siteUrl()}/kopvillkor`;
  const m = momsspec(opts.amountSek);

  const htmlBody = `
    <div style="font-family:Arial,Helvetica,sans-serif;color:#111;line-height:1.5">
      <h2 style="margin:0 0 12px">Din lönerapport är klar</h2>
      <p>Tack för ditt köp. Rapporten bygger på faktiska, utlämnade löner enligt
        offentlighetsprincipen – ett faktaunderlag att ta med till lönesamtalet.</p>
      <p>Din rapport finns här:</p>
      <p style="margin:20px 0">
        <a href="${url}"
           style="background:#2563eb;color:#fff;text-decoration:none;
                  padding:12px 20px;border-radius:6px;display:inline-block">
          Öppna lönerapporten
        </a>
      </p>
      <p style="font-size:13px;color:#555">
        Länken är giltig t.o.m. <strong>${expiry}</strong>. Spara den – den fungerar
        utan inloggning. Du kan skriva ut rapporten eller spara den som PDF från
        rapportsidan.
      </p>
      <p style="font-size:13px;color:#555">
        Om knappen inte fungerar, kopiera denna adress till webbläsaren:<br>
        <span style="word-break:break-all">${url}</span>
      </p>

      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <h3 style="font-size:14px;margin:0 0 8px">Orderbekräftelse</h3>
      <table style="font-size:13px;color:#333;border-collapse:collapse">
        <tr><td style="padding:2px 14px 2px 0;color:#777">Köpdatum</td><td>${purchased}</td></tr>
        <tr><td style="padding:2px 14px 2px 0;color:#777">Orderreferens</td><td style="word-break:break-all">${opts.orderRef}</td></tr>
        <tr><td style="padding:2px 14px 2px 0;color:#777">Produkt</td><td>Lönerapport (digital), levererad direkt</td></tr>
        <tr><td style="padding:2px 14px 2px 0;color:#777">Pris exkl. moms</td><td>${m.exklMoms} kr</td></tr>
        <tr><td style="padding:2px 14px 2px 0;color:#777">Moms ${m.satsProcent} %</td><td>${m.moms} kr</td></tr>
        <tr><td style="padding:2px 14px 2px 0;color:#777">Att betala</td><td><strong>${m.brutto} kr</strong></td></tr>
      </table>
      <p style="font-size:13px;color:#555;margin-top:12px">
        Du har samtyckt till att rapporten levereras omedelbart och bekräftat att
        ångerrätten därmed går förlorad när tjänsten fullgjorts. Köpet omfattas av
        våra <a href="${kopvillkorUrl}">köpvillkor</a>.
      </p>
      <p style="font-size:13px;color:#555">
        Vi lämnar ändå 30 dagars nöjd-kund-garanti: är du inte nöjd, mejla
        <a href="mailto:kontakt@offentligaloner.se">kontakt@offentligaloner.se</a>
        inom 30 dagar från köpet så får du pengarna tillbaka.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="font-size:12px;color:#888;margin:0 0 8px">
        Patrik Larsson, enskild näringsidkare<br>
        Organisationsnummer 890405-4676<br>
        Momsreg.nr SE890405467601 · Godkänd för F-skatt
      </p>
      <p style="font-size:12px;color:#888">
        Offentliga löner, offentligaloner.se · Utgivningsbevis nr 2024-077.
        Rapporten bygger på aggregerad lönestatistik (minst 5 individer per uppgift);
        ingen individdata visas.
      </p>
    </div>`.trim();

  const textBody = [
    "Din lönerapport är klar",
    "",
    "Tack för ditt köp. Rapporten bygger på faktiska, utlämnade löner enligt " +
      "offentlighetsprincipen – ett faktaunderlag att ta med till lönesamtalet.",
    "",
    "Öppna rapporten här:",
    url,
    "",
    `Länken är giltig t.o.m. ${expiry}. Spara den – den fungerar utan inloggning.`,
    "",
    "--- Orderbekräftelse ---",
    `Köpdatum: ${purchased}`,
    `Orderreferens: ${opts.orderRef}`,
    "Produkt: Lönerapport (digital), levererad direkt",
    `Pris exkl. moms: ${m.exklMoms} kr`,
    `Moms ${m.satsProcent} %: ${m.moms} kr`,
    `Att betala: ${m.brutto} kr`,
    "",
    "Du har samtyckt till att rapporten levereras omedelbart och bekräftat att " +
      "ångerrätten därmed går förlorad när tjänsten fullgjorts. Köpet omfattas av " +
      `våra köpvillkor: ${kopvillkorUrl}`,
    "",
    "Vi lämnar ändå 30 dagars nöjd-kund-garanti: är du inte nöjd, mejla " +
      "kontakt@offentligaloner.se inom 30 dagar från köpet så får du pengarna tillbaka.",
    "",
    "Patrik Larsson, enskild näringsidkare",
    "Organisationsnummer 890405-4676",
    "Momsreg.nr SE890405467601 · Godkänd för F-skatt",
    "",
    "Offentliga löner, offentligaloner.se · Utgivningsbevis nr 2024-077.",
  ].join("\n");

  return postmarkSend({
    to: opts.to,
    subject: "Din lönerapport från Offentliga löner",
    htmlBody,
    textBody,
  });
}

// Ommejling av EN eller FLERA giltiga rapportlänkar för samma adress
// (/rapport/skicka-igen). Anropas bara när det finns giltiga länkar.
export async function sendResendEmail(opts: {
  to: string;
  links: { token: string; expiresAt: Date }[];
}): Promise<SendResult> {
  const items = opts.links.map((l) => {
    const url = reportUrl(l.token);
    return { url, expiry: formatDate(l.expiresAt) };
  });

  const htmlList = items
    .map(
      (i) =>
        `<li style="margin:8px 0">
           <a href="${i.url}" style="color:#2563eb;word-break:break-all">${i.url}</a>
           <br><span style="font-size:12px;color:#888">Giltig t.o.m. ${i.expiry}</span>
         </li>`,
    )
    .join("");

  const htmlBody = `
    <div style="font-family:Arial,Helvetica,sans-serif;color:#111;line-height:1.5">
      <h2 style="margin:0 0 12px">Dina lönerapporter</h2>
      <p>Här är dina giltiga rapportlänkar:</p>
      <ul style="padding-left:18px">${htmlList}</ul>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="font-size:12px;color:#888">
        Offentliga löner, offentligaloner.se · Utgivningsbevis nr 2024-077.
      </p>
    </div>`.trim();

  const textBody = [
    "Dina lönerapporter",
    "",
    ...items.flatMap((i) => [i.url, `Giltig t.o.m. ${i.expiry}`, ""]),
    "Offentliga löner, offentligaloner.se",
  ].join("\n");

  return postmarkSend({
    to: opts.to,
    subject: "Dina lönerapporter från Offentliga löner",
    htmlBody,
    textBody,
  });
}
