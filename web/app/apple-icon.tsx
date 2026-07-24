// Apple-touch-icon (180×180) genererad ur samma logotypgeometri som icon.svg.
// Byggs vid deploy via next/og (satori). Staplarna positioneras absolut, skalade
// med faktorn 180/64 = 2.8125 från viewBox-64.
import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  const bar = (
    left: number,
    top: number,
    height: number,
    color: string,
  ) => (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width: 25.3,
        height,
        borderRadius: 13,
        background: color,
      }}
    />
  );

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#0C447C",
          borderRadius: 42,
          display: "flex",
          position: "relative",
        }}
      >
        {bar(36.6, 95.6, 42.2, "#378ADD")}
        {bar(77.3, 73.1, 64.7, "#85B7EB")}
        {bar(118.1, 50.6, 87.2, "#FFFFFF")}
        <div
          style={{
            position: "absolute",
            left: 119.5,
            top: 19.6,
            width: 22.5,
            height: 22.5,
            borderRadius: 12,
            background: "#F0997B",
          }}
        />
      </div>
    ),
    { ...size },
  );
}
