// DaranX logo mark — an abstract crossing / connecting form that reinforces
// the idea of connection and parts coming together in the right place.
// Uses only the brand palette (navy + accent tint). Purely decorative.
export default function Logo({ size = 40, tone = "navy" }) {
  const primary = tone === "light" ? "#ffffff" : "#153a62";
  const secondary = tone === "light" ? "#8fb4e6" : "#2f6bd6";
  return (
    <svg
      className="logo-mark"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label="DaranX"
      style={{ width: size, height: size }}
    >
      <rect x="2" y="2" width="44" height="44" rx="12" fill={primary} />
      {/* Crossing strokes: two paths meeting at the center — "in its right place" */}
      <path
        d="M14 14 L34 34"
        stroke={secondary}
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <path
        d="M34 14 L14 34"
        stroke="#ffffff"
        strokeWidth="4.5"
        strokeLinecap="round"
        opacity={tone === "light" ? 0.85 : 0.92}
      />
      <circle cx="24" cy="24" r="3.4" fill={tone === "light" ? primary : "#ffffff"} />
    </svg>
  );
}
