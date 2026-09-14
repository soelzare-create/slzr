import { services } from "../data.js";

const icons = {
  infrastructure: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="4" width="18" height="5" rx="1.5" />
      <rect x="3" y="15" width="18" height="5" rx="1.5" />
      <path d="M7 6.5h.01M7 17.5h.01" strokeLinecap="round" />
    </svg>
  ),
  security: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  intelligence: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3v3M12 18v3M3 12h3M18 12h3M6 6l2 2M16 16l2 2M18 6l-2 2M8 16l-2 2" strokeLinecap="round" />
    </svg>
  ),
};

// Infrastructure · Security · Intelligence (Brand Skill §7)
export default function Services() {
  return (
    <section className="section section-tint" id="services">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">معماری خدمات</span>
          <h2>سه حوزه، یک راهکار</h2>
          <p>
            توانمندی‌های DaranX در سه حوزه‌ی اصلی قرار می‌گیرند. تمایز ما در تعداد
            خدمات نیست؛ در طراحیِ ارتباط میان این حوزه‌هاست.
          </p>
        </div>

        <div className="grid grid-3">
          {services.map((s) => (
            <article className="card hover service-card" key={s.key}>
              <span className="svc-ico">{icons[s.key]}</span>
              <h3>
                {s.title}
                <span style={{ color: "var(--muted-2)", fontWeight: 500, fontSize: 15 }}>
                  {" "}· {s.fa}
                </span>
              </h3>
              <p style={{ color: "var(--accent)", fontWeight: 600, marginBottom: 8 }}>
                {s.tagline}
              </p>
              <p>{s.desc}</p>
              <ul>
                {s.items.map((it) => (
                  <li key={it}>{it}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
