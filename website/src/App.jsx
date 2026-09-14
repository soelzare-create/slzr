import Header from "./components/Header.jsx";
import Hero from "./components/Hero.jsx";
import Philosophy from "./components/Philosophy.jsx";
import Method from "./components/Method.jsx";
import Services from "./components/Services.jsx";
import DesignLayer from "./components/DesignLayer.jsx";
import Differentiator from "./components/Differentiator.jsx";
import Positioning from "./components/Positioning.jsx";
import Ventures from "./components/Ventures.jsx";
import Contact from "./components/Contact.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Philosophy />
        <Method />
        <Services />
        <DesignLayer />
        <Differentiator />
        <Positioning />
        <Ventures />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
