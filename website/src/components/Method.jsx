import { method } from "../data.js";

// شناخت ← طراحی ← اجرا ← پشتیبانی
export default function Method() {
  return (
    <section className="section" id="method">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">روش DaranX</span>
          <h2>شناخت ← طراحی ← اجرا ← پشتیبانی</h2>
          <p>
            روش ما یک زنجیره‌ی پیوسته است، نه چند خدمت جدا. هر مرحله پایه‌ی مرحله‌ی
            بعد است و پشتیبانی از همان مرحله‌ی طراحی آغاز می‌شود.
          </p>
        </div>

        <div className="grid grid-4">
          {method.map((m, i) => (
            <article className="card hover step-card" key={m.key}>
              <span className="step-num">{i + 1}</span>
              <h3>{m.title}</h3>
              <p>{m.desc}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
