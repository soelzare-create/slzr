import Logo from "./Logo.jsx";
import { brand, nav, services } from "../data.js";

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="site-footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">
              <Logo size={40} tone="light" />
              <span className="name">{brand.name}</span>
            </div>
            <p className="footer-about">
              شریک فناوری سازمان‌ها و کسب‌وکارها. زیرساخت، امنیت و فناوری‌های هوشمند
              را طراحی، اجرا و پشتیبانی می‌کنیم — با این باور که همه چیز باید سر جای
              درستش باشد.
            </p>
          </div>

          <div>
            <h4>حوزه‌ها</h4>
            {services.map((s) => (
              <a key={s.key} href="#services">
                {s.title}
              </a>
            ))}
          </div>

          <div>
            <h4>پیوندها</h4>
            {nav.map((n) => (
              <a key={n.href} href={n.href}>
                {n.label}
              </a>
            ))}
          </div>
        </div>

        <div className="footer-bottom">
          <span className="footer-tagline">{brand.coreIdea}</span>
          <span>© {year} {brand.name}. تمامی حقوق محفوظ است.</span>
        </div>
      </div>
    </footer>
  );
}
