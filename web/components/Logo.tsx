// Logotypsymbol – v1-identitetens hexagon, ren kontur i primär teal (#166F81).
// Används i rapportens dokumenthuvud bredvid ordbilden. Samma geometri som
// faviconen (spetsig topp/botten, lodräta sidor). Inga staplar/triangel och
// inga brokiga v1-logofärger – de lever bara i den fulla logotypfilen.

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
      height={(size * 64) / 56}
      viewBox="0 0 56 64"
      className={className}
      role="img"
      aria-label="Offentliga löner"
    >
      <polygon
        points="28,4 52.25,18 52.25,46 28,60 3.75,46 3.75,18"
        fill="none"
        stroke="#166F81"
        strokeWidth="6"
        strokeLinejoin="round"
      />
    </svg>
  );
}
