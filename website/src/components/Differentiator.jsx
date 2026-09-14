import { brand, differentiators } from "../data.js";

// Brand differentiation (Brand Skill §6)
export default function Differentiator() {
  return (
    <section className="section">
      <div className="container pos-grid">
        <div>
          <span className="eyebrow">تمایز ما</span>
          <p className="diff-quote">{brand.differentiator}</p>
        </div>
        <div>
          <p style={{ color: "var(--muted)", fontSize: 17 }}>
            ارزش واقعی زمانی ایجاد می‌شود که اجزای مختلف با یک منطق مشترک کنار هم
            قرار بگیرند:
          </p>
          <ul className="diff-list">
            {differentiators.map((d) => (
              <li key={d}>
                <span className="tick">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <path d="M5 12l5 5 9-11" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
                {d}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
