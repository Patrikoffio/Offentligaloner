// OG-bild (1200×630) – samma källa som faviconen: v1-hexagonen i primär teal
// bredvid ordbilden, på ljus yta i v1-paletten. Byggs via next/og (standardfont).
import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "Offentliga löner – lönestatistik för offentlig sektor";

const hexagon =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 56 64">' +
      '<polygon points="28,4 52.25,18 52.25,46 28,60 3.75,46 3.75,18" ' +
      'fill="none" stroke="#166F81" stroke-width="6" stroke-linejoin="round"/>' +
      "</svg>",
  );

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#FFFFFF",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "0 96px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={hexagon} width={132} height={151} alt="" />
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 76, fontWeight: 600, color: "#166F81" }}>
              Offentliga löner
            </div>
            <div style={{ fontSize: 34, color: "#5A6A6C", marginTop: 8 }}>
              offentligaloner.se
            </div>
          </div>
        </div>
        <div
          style={{
            fontSize: 34,
            color: "#13201F",
            marginTop: 56,
            maxWidth: 940,
            lineHeight: 1.35,
          }}
        >
          Faktiska löner i kommuner och regioner, utlämnade enligt
          offentlighetsprincipen.
        </div>
      </div>
    ),
    { ...size },
  );
}
