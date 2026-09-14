import { brand } from "../data.js";

// Closing CTA (Brand Skill §11 promise). Placeholder contact endpoints —
// replace with real channels when available.
export default function Contact() {
  return (
    <section className="section section-navy cta" id="contact">
      <div className="container">
        <span className="eyebrow" style={{ justifyContent: "center" }}>
          گفت‌وگو را شروع کنیم
        </span>
        <h2>{brand.promise}</h2>
        <p>
          اول نیاز شما را مشخص می‌کنیم؛ بعد می‌گوییم چه چیزی واقعاً لازم دارید. برای
          شروع، مسئله‌ی سازمان‌تان را با ما در میان بگذارید.
        </p>
        <div className="cta-actions">
          <a className="btn on-navy" href="mailto:hello@daranx.example">
            info@daranx.ir
          </a>
          <a className="btn ghost" href="tel:+980000000000" style={{ color: "#dfe7f0", borderColor: "rgba(255,255,255,0.3)" }}>
            درخواست تماس
          </a>
        </div>
      </div>
    </section>
  );
}
