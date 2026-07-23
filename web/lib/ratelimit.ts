// Enkel in-memory rate-limiter (best-effort). Skyddar /rapport/skicka-igen mot
// enumeration/spam. OBS: per serverinstans – i en flerinstansmiljö delas inte
// räknaren. Räcker som första barriär; kombineras med generiskt svar (inget
// läckage om en adress finns eller ej).
type Bucket = { count: number; resetAt: number };

const buckets = new Map<string, Bucket>();

// Rensar utgångna nycklar l+ ivrigt vid varje anrop (håller minnet litet).
function sweep(now: number) {
  for (const [key, b] of buckets) {
    if (b.resetAt <= now) buckets.delete(key);
  }
}

// Returnerar true om anropet TILLÅTS, false om kvoten är slut.
export function rateLimit(key: string, max: number, windowMs: number): boolean {
  const now = Date.now();
  sweep(now);
  const b = buckets.get(key);
  if (!b || b.resetAt <= now) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }
  if (b.count >= max) return false;
  b.count += 1;
  return true;
}

// Klient-IP ur standardproxy-headers (Vercel sätter x-forwarded-for).
export function clientIp(req: Request): string {
  const xff = req.headers.get("x-forwarded-for");
  if (xff) return xff.split(",")[0].trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}
