import { planogram } from "../data.js";

// PlanoGram venture (Brand Skill §16). No new capabilities or business claims
// are added here beyond what the Brand Skill states.
export default function Ventures() {
  return (
    <section className="section" id="planogram">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">Ventures</span>
          <h2>محصولات مستقل در اکوسیستم DaranX</h2>
          <p>
            علاوه بر حوزه‌های اصلی، DaranX از Venture‌های مستقلی پشتیبانی می‌کند که
            همان منطق برند را در بازار خودشان دنبال می‌کنند.
          </p>
        </div>

        <div className="venture">
          <div>
            <span className="tag">{planogram.tag}</span>
            <h3>{planogram.name}</h3>
            <p>{planogram.desc}</p>
            <ul>
              {planogram.capabilities.map((c) => (
                <li key={c}>
                  <span className="b" />
                  {c}
                </li>
              ))}
            </ul>
          </div>

          <div className="venture-map" aria-hidden="true">
            <div className="root">DaranX</div>
            <div className="branch"><span className="line">├─</span> Infrastructure</div>
            <div className="branch"><span className="line">├─</span> Security</div>
            <div className="branch"><span className="line">├─</span> Intelligence</div>
            <div className="branch"><span className="line">└─</span> Ventures</div>
            <div className="branch child"><span className="line">└─</span> {planogram.name}</div>
          </div>
        </div>
      </div>
    </section>
  );
}
