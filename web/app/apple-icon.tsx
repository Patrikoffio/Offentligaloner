// Apple-touch-icon (180×180) – SAMMA flerfärgade v1-hexagon som favicon.ico +
// app/icon.png (härledd ur public/offlon-symbol.svg), centrerad på vit rundad
// yta. Byggs vid deploy via next/og. Inline fill-attribut (inte style=) så resvg
// rasteriserar färgerna korrekt.
import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

const symbol =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -0.010009765625 479.760009765625 554">' +
      '<polygon points="214.06 291.87 214.06 470.66 162.42 440.85 162.42 321.67 214.06 291.87" fill="#589F44"/>' +
      '<polygon points="110.79 411.05 110.79 351.49 59.26 381.24 110.79 411.05" fill="#F0B71C"/>' +
      '<polygon points="317.27 232.27 317.27 440.85 265.64 470.66 265.64 262.08 317.27 232.27" fill="#1D92B4"/>' +
      '<polygon points="239.86 68.37 188.22 98.17 368.88 202.47 368.88 411.06 420.5 381.26 420.5 172.67 239.86 68.37" fill="#166F81"/>' +
      '<path d="M1000,1277,760.12,1138.5v-277L1000,723,1239.88,861.5v277ZM775.49,1129.62,1000,1259.24l224.51-129.62V870.38L1000,740.76,775.49,870.38Z" transform="translate(-760.12 -723.01)" fill="#166F81"/>' +
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
        <img src={symbol} width={130} height={150} alt="" />
      </div>
    ),
    { ...size },
  );
}
