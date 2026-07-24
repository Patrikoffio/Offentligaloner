// Betalförtroende. Enligt beslut: enbart textraden "Säker betalning via Stripe"
// (inga betalmärken – officiella brand-assets fanns inte att tillgå och egna
// får inte ritas).
export default function PaymentMarks({
  className = "",
  center = false,
}: {
  className?: string;
  center?: boolean;
}) {
  return (
    <div
      className={`flex items-center ${center ? "justify-center" : ""} ${className}`}
    >
      <span className="text-xs text-gray-500">Säker betalning via Stripe</span>
    </div>
  );
}
