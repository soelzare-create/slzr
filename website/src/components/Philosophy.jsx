import { brand } from "../data.js";

// Brand philosophy band (Brand Skill §2 & §3): design precedes execution,
// and the core belief that precise execution of a wrong design is still wrong.
export default function Philosophy() {
  return (
    <section className="section section-navy statement">
      <div className="container">
        <span className="eyebrow">فلسفه برند</span>
        <p className="quote">{brand.philosophy}</p>
        <p className="sub">{brand.belief}</p>
      </div>
    </section>
  );
}
