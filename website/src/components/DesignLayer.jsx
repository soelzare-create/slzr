import { services } from "../data.js";

// Shared design layer (Brand Skill §8): Design is not a service next to the
// others — it is the layer that connects Infrastructure, Security & Intelligence.
export default function DesignLayer() {
  return (
    <section className="section section-navy" id="design">
      <div className="container">
        <div className="section-head" style={{ marginInline: "auto", textAlign: "center", maxWidth: 760 }}>
          <span className="eyebrow" style={{ justifyContent: "center" }}>
            لایه‌ی مشترک
          </span>
          <h2>Design یک خدمت در کنار بقیه نیست</h2>
          <p>
            طراحی، لایه‌ای است که همه‌ی حوزه‌ها را به هم متصل می‌کند. ابتدا طراحی
            می‌کنیم که هر حوزه چگونه ساخته شود، چگونه محافظت شود و چگونه ارزش بسازد.
          </p>
        </div>

        <div className="design-diagram">
          <div className="design-node">Design</div>

          <svg className="design-connectors" viewBox="0 0 560 46" fill="none" aria-hidden="true">
            <path d="M280 0 V16" stroke="#5f7ea3" strokeWidth="2" />
            <path d="M280 16 H94 V46 M280 16 H466 V46 M280 16 V46" stroke="#5f7ea3" strokeWidth="2" />
            <circle cx="94" cy="46" r="3" fill="#8fb4e6" />
            <circle cx="280" cy="46" r="3" fill="#8fb4e6" />
            <circle cx="466" cy="46" r="3" fill="#8fb4e6" />
          </svg>

          <div className="design-children">
            {services.map((s) => (
              <div className="design-child" key={s.key}>
                {s.title}
              </div>
            ))}
          </div>
        </div>

        <p className="formula">
          Design <span className="op">+</span> Technology <span className="op">=</span> Solution
        </p>
      </div>
    </section>
  );
}
