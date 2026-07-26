// Apple-touch-icon (180×180) – samma källa som faviconen: v1-hexagonens kontur
// i primär teal (#166F81) på ljus yta. Byggs vid deploy via next/og.
import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

// Hexagon-kontur som data-URI (satori renderar SVG-bilder via resvg).
const hexagon =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 64">' +
      '<polygon points="28,4 52.25,18 52.25,46 28,60 3.75,46 3.75,18" ' +
      'fill="none" stroke="#166F81" stroke-width="6" stroke-linejoin="round"/>' +
      "</svg>",
  );

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#FFFFFF",
          borderRadius: 42,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={hexagon} width={104} height={119} alt="" />
      </div>
    ),
    { ...size },
  );
}
