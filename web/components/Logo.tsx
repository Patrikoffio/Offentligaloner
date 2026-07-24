// Logotyp – Offentliga löner.
// Mörkblå rundad kvadrat + tre stigande staplar (helt rundade ändar) i fallande
// blåtoner till vitt + svävande orange cirkel över den högsta stapeln.
// Geometrin är låst i viewBox 64 (samma som favicon/apple-touch-icon).

export default function Logo({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="Offentliga löner"
    >
      {/* Bakgrund: rundad kvadrat, radius ~23 % av sidan */}
      <rect width="64" height="64" rx="15" fill="#0C447C" />
      {/* Tre stigande staplar, pill-form (rx = halva bredden) */}
      <rect x="13" y="34" width="9" height="15" rx="4.5" fill="#378ADD" />
      <rect x="27.5" y="26" width="9" height="23" rx="4.5" fill="#85B7EB" />
      <rect x="42" y="18" width="9" height="31" rx="4.5" fill="#FFFFFF" />
      {/* Orange cirkel, svävar över den högsta stapeln */}
      <circle cx="46.5" cy="11" r="4" fill="#F0997B" />
    </svg>
  );
}
