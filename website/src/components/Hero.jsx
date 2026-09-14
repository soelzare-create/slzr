import { brand, method } from "../data.js";

export default function Hero() {
  return (
    <section className="hero" id="top">
      <div className="container hero-grid">
        <div className="hero-copy">
          <span className="eyebrow">{brand.positioning}</span>
          <h1>
            همه چیز <span className="accent">سر جای درستش.</span>
          </h1>
          <p className="lead">
            DaranX زیرساخت، امنیت و فناوری‌های هوشمند را از شناخت و طراحی تا اجرا و
            پشتیبانی، به‌عنوان اجزای یک راهکار واحد می‌بیند.
          </p>

          <div className="hero-actions">
            <a className="btn primary" href="#contact">
              شروع یک گفت‌وگو
            </a>
            <a className="btn ghost" href="#method">
              روش کار ما
            </a>
          </div>

          <div className="hero-chain">
            <div className="chain" aria-label="روش کار: شناخت، طراحی، اجرا، پشتیبانی">
              {method.map((m, i) => (
                <span key={m.key} style={{ display: "contents" }}>
                  <span className="step">
                    <span className="dot" />
                    {m.title}
                  </span>
                  {i < method.length - 1 && <span className="arrow">←</span>}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="hv-head">
            <span className="hv-title">راهکار منسجم</span>
            <span className="hv-tag">Design + Technology</span>
          </div>

          {[
            { t: "Infrastructure", s: "بستر پایدار و قابل توسعه" },
            { t: "Security", s: "محافظت از محیط و دسترسی‌ها" },
            { t: "Intelligence", s: "داده و تصمیم‌گیری هوشمند" },
          ].map((row) => (
            <div className="stack-row" key={row.t}>
              <span className="ico">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8fb4e6" strokeWidth="2">
                  <path d="M5 12l5 5 9-11" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <span className="rt">
                <b>{row.t}</b>
                <span>{row.s}</span>
              </span>
              <span className="ok">سر جای خود</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
