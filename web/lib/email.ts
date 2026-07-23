// Postmark-utskick (ENDAST server-side) via HTTP-API – ingen extra dependency.
// Samma Postmark-konto som gamla sajten; avsändare no-reply@offentligaloner.se.
// POSTMARK_SERVER_TOKEN får aldrig NEXT_PUBLIC-prefix.
import { reportUrl } from "./site";

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
}): Promise<SendResult> {
  const url = reportUrl(opts.token);
  const expiry = formatDate(opts.expiresAt);

  const htmlBody = `
    <div style="font-family:Arial,Helvetica,sans-serif;color:#111;line-height:1.5">
      <h2 style="margin:0 0 12px">Din lönerapport är klar</h2>
      <p>Tack för ditt köp. Din rapport finns här:</p>
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
      <p style="font-size:12px;color:#888">
        Offentliga löner, offentligaloner.se · Utgivningsbevis nr 2024-077.
        Rapporten bygger på aggregerad lönestatistik (minst 5 individer per uppgift);
        ingen individdata visas.
      </p>
    </div>`.trim();

  const textBody = [
    "Din lönerapport är klar",
    "",
    "Tack för ditt köp. Öppna rapporten här:",
    url,
    "",
    `Länken är giltig t.o.m. ${expiry}. Spara den – den fungerar utan inloggning.`,
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
