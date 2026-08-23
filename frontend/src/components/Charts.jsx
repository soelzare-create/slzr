import React from "react";

// Dependency-free SVG charts, styled from the CSS custom properties.
const fa = (n) => Number(n || 0).toLocaleString("fa-IR");

export function Pill({ tone = "", children }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

export function KpiCard({ label, value, note, tone }) {
  return (
    <div className="stat">
      <div className="kpi-label">{label}</div>
      <div className={`stat-num ${tone || ""}`} style={toneColor(tone)}>
        {typeof value === "number" ? fa(value) : value}
      </div>
      {note && <div className="kpi-note">{note}</div>}
    </div>
  );
}

function toneColor(tone) {
  if (tone === "warn") return { color: "var(--warn)" };
  if (tone === "bad") return { color: "var(--danger)" };
  if (tone === "ok") return { color: "var(--ok)" };
  return undefined;
}

// Horizontal ranked bars — top debtors, expense categories, …
export function RankBars({ items, color = "var(--navy)", altColor }) {
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 13 }}>
      {items.length === 0 && (
        <div style={{ fontSize: 12.5, color: "var(--text-3)" }}>موردی نیست</div>
      )}
      {items.map((it, i) => (
        <div key={it.key ?? it.name ?? i}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 12.5,
              marginBottom: 6,
            }}
          >
            <span>{it.name}</span>
            <span className="num" style={{ color: "var(--text-2)" }}>
              {fa(it.value)}
            </span>
          </div>
          <div
            style={{
              height: 7,
              borderRadius: 99,
              background: "var(--surface-3)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                borderRadius: 99,
                width: `${Math.max(2, (Math.abs(it.value) / max) * 100)}%`,
                background: altColor && i > 1 ? altColor : color,
                transition: "width .5s ease",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// Donut / ring chart. segments: [{label, value, color}]
export function Donut({ segments, size = 148, thickness = 18, centerLabel, centerValue }) {
  const total = segments.reduce((s, x) => s + Math.max(0, x.value), 0);
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  let offset = 0;

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img">
        <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="var(--surface-3)"
            strokeWidth={thickness}
          />
          {total > 0 &&
            segments.map((s, i) => {
              const len = (Math.max(0, s.value) / total) * c;
              const el = (
                <circle
                  key={i}
                  cx={size / 2}
                  cy={size / 2}
                  r={r}
                  fill="none"
                  stroke={s.color}
                  strokeWidth={thickness}
                  strokeDasharray={`${len} ${c - len}`}
                  strokeDashoffset={-offset}
                  strokeLinecap="butt"
                />
              );
              offset += len;
              return el;
            })}
        </g>
        {(centerValue || centerLabel) && (
          <>
            <text
              x="50%"
              y="47%"
              textAnchor="middle"
              style={{
                fontSize: 17,
                fontWeight: 600,
                fill: "var(--text)",
                fontVariantNumeric: "tabular-nums",
              }}
            >
              {centerValue}
            </text>
            <text
              x="50%"
              y="62%"
              textAnchor="middle"
              style={{ fontSize: 10.5, fill: "var(--text-3)" }}
            >
              {centerLabel}
            </text>
          </>
        )}
      </svg>
      <div style={{ flex: 1, minWidth: 150 }}>
        {segments.map((s, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              fontSize: 12.5,
              padding: "5px 0",
            }}
          >
            <span
              className="dot"
              style={{
                width: 8,
                height: 8,
                borderRadius: 50,
                background: s.color,
                flex: "none",
              }}
            />
            <span style={{ color: "var(--text-2)", flex: 1 }}>{s.label}</span>
            <b className="num">{fa(s.value)}</b>
          </div>
        ))}
      </div>
    </div>
  );
}

// Sparkline / area trend. points: number[]
export function Trend({ points, width = 320, height = 96, color = "var(--navy)" }) {
  if (!points || points.length < 2) return null;
  const max = Math.max(...points, 1);
  const min = Math.min(...points, 0);
  const span = max - min || 1;
  const step = width / (points.length - 1);
  const xy = points.map((p, i) => [
    i * step,
    height - ((p - min) / span) * (height - 8) - 4,
  ]);
  const line = xy.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity=".22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#trendFill)" />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
      {xy.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="2.5" fill={color} />
      ))}
    </svg>
  );
}

// Grouped vertical columns — e.g. income vs expense side by side.
export function Columns({ groups, height = 150 }) {
  const max = Math.max(...groups.flatMap((g) => g.values.map((v) => v.value)), 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 22, height, marginTop: 8 }}>
      {groups.map((g) => (
        <div
          key={g.label}
          style={{ flex: 1, display: "flex", flexDirection: "column", height: "100%" }}
        >
          <div style={{ flex: 1, display: "flex", alignItems: "flex-end", gap: 6 }}>
            {g.values.map((v) => (
              <div
                key={v.label}
                title={`${v.label}: ${fa(v.value)}`}
                style={{
                  flex: 1,
                  height: `${Math.max(2, (v.value / max) * 100)}%`,
                  background: v.color,
                  borderRadius: "6px 6px 0 0",
                  transition: "height .5s ease",
                }}
              />
            ))}
          </div>
          <div
            style={{
              fontSize: 11.5,
              color: "var(--text-3)",
              textAlign: "center",
              marginTop: 8,
            }}
          >
            {g.label}
          </div>
        </div>
      ))}
    </div>
  );
}

export { fa };
