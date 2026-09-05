import heroImage from "./assets/hero.jpg";
import heroVideo from "./assets/hero_loop.mp4";
import secureImage from "./assets/secure.jpg";
import aiImage from "./assets/ai.jpg";
import sustainabilityImage from "./assets/sustainability.jpg";
import modesImage from "./assets/modes.jpg";
import xpsImage from "./assets/xps.png";
import da305Image from "./assets/da305.png";
import da326Image from "./assets/da326.png";
import jblImage from "./assets/jbl.png";

const features = [
  { title: "Secure and reliable", image: secureImage },
  { title: "New AI experiences", image: aiImage },
  { title: "Built-in sustainability", image: sustainabilityImage },
  { title: "Powered by four modes", image: modesImage },
];

const products = [
  { title: "Dell XPS 13", image: xpsImage },
  { title: "ACCESSORIES", model: "DA305", image: da305Image },
  { title: "ACCESSORIES", model: "DA326", image: da326Image },
  { title: "SPECIAL OFFERS", image: jblImage },
];

// Hero example:
// <video className="hero-video" autoPlay muted loop playsInline poster={heroImage}>
//   <source src={heroVideo} type="video/mp4" />
// </video>
