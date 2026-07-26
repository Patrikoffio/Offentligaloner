// Logotyp – v1-identiteten (symbol + ordbild) som INLINE-SVG. Inline är ett krav:
// loggan renderas bl.a. i lönerapportens dokumenthuvud, som är en utskrifts-/PDF-
// produkt där en <img>-SVG inte är garanterad i tryck. Själva SVG-strängen ligger
// i logo-svg.ts (enda logokällan i komponentform) så en logga-/palettändring blir
// en filändring där, utan att röra den här komponenten.
//
// LOGO_SVG är en statisk sträng ur egen kodbas (aldrig användardata) – därför är
// dangerouslySetInnerHTML säkert här. Storlek styrs via className på wrappern;
// den inre svg:n fyller höjden och behåller sitt bredd/höjd-förhållande.
import { LOGO_SVG } from "./logo-svg";

export default function Logo({ className }: { className?: string }) {
  return (
    <span
      className={`inline-block [&>svg]:block [&>svg]:h-full [&>svg]:w-auto${
        className ? ` ${className}` : ""
      }`}
      role="img"
      aria-label="Offentliga löner"
      dangerouslySetInnerHTML={{ __html: LOGO_SVG }}
    />
  );
}
