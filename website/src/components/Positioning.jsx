import { brand, positioning } from "../data.js";

// Brand positioning (Brand Skill §9): what DaranX is not, and what it is.
export default function Positioning() {
  return (
    <section className="section section-tint">
      <div className="container pos-grid">
        <div>
          <span className="eyebrow">جایگاه برند</span>
          <h2 style={{ fontSize: "clamp(26px, 3.6vw, 40px)", fontWeight: 800 }}>
            {brand.positioning}
          </h2>
          <p style={{ color: "var(--muted)", fontSize: 17, marginTop: 16 }}>
            DaranX زیرساخت، امنیت و فناوری‌های هوشمند را از مرحله‌ی شناخت و طراحی تا
            اجرا و پشتیبانی، به‌عنوان اجزای یک راهکار واحد می‌بیند.
          </p>
        </div>

        <div className="notjust">
          {positioning.not.map((n) => (
            <div className="row" key={n}>
              <span className="x">✕</span>
              {n}
            </div>
          ))}
          <div className="row is">
            <span className="x">✓</span>
            <span>
              <b>{positioning.is}</b>
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
