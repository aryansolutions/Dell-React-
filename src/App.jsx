import { useRef, useState } from "react";
import "./App.css";

import heroVideo from "./assets/hero_loop.mp4";
import heroImg from "./assets/hero.jpg";

import secure from "./assets/secure.jpg";
import ai from "./assets/ai.jpg";
import sustainability from "./assets/sustainability.jpg";
import modes from "./assets/modes.jpg";

import xps from "./assets/xps.png";
import da305 from "./assets/da305.png";
import da326 from "./assets/da326.png";
import jbl from "./assets/jbl.png";

function App() {

  const [fi, setFi] = useState(0);
  const [zoom, setZoom] = useState(null);
  const [pi, setPi] = useState(0);
  const [dir, setDir] = useState("right");
  const [playing, setPlaying] = useState(true);

  const video = useRef();

  const features = [
    { title: "Secure and reliable", img: secure, icon: "◈", text: "Designed for dependable and secure everyday computing." },

    { title: "New AI experiences", img: ai, icon: "AI", text: "Sleek 14-inch 2-in-1 with on-device Copilot+ powered by Intel Core Ultra processors, with stunning performance that powers the newest AI experiences." },

    { title: "Built-in sustainability", img: sustainability, icon: "♻", text: "Designed with sustainability in mind while delivering modern performance." },

    { title: "Powered by four modes", img: modes, icon: "✦", text: "Switch between different modes for work, entertainment and creativity." }
  ];

  const products = [
    { type: "xps", title: "Dell XPS 13", sub: "Starting from", price: "₹53,364", emi: "EMI starting at ₹2,224", img: xps },

    { title: "ACCESSORIES", sub: "Dell 6-in-1 USB-C Multiport Adapter", model: "DA305", price: "₹9,999/-* at ₹1,999/-*", img: da305 },

    { title: "ACCESSORIES", sub: "Dell Pro 7-in-1 USB-C Travel Hub", model: "DA326", price: "₹9,999/-* at ₹1,999/-*", img: da326 },

    { type: "offer", title: "SPECIAL OFFERS", sub: "JBL Tune 770NC Headphones worth", price: "₹9,999/-* at ₹1,999/-*", img: jbl }
  ];

  // feature slider

  function nextF() {
    setZoom(null);
    setFi((fi + 1) % features.length);
  }

  function prevF() {
    setZoom(null);
    setFi((fi - 1 + features.length) % features.length);
  }

  function cardClick(i) {
    if (i !== fi) {
      setFi(i);
      setZoom(null);
    } else {
      setZoom(zoom === i ? null : i);
    }
  }

  // product slider

  function nextP() {
    setDir("right");
    setPi((pi + 1) % products.length);
  }

  function prevP() {
    setDir("left");
    setPi((pi - 1 + products.length) % products.length);
  }

  // video

  function videoPlay() {
    if (!video.current) return;

    if (video.current.paused) video.current.play();
    else video.current.pause();
  }

  const p = products[pi];

  return (
    <div className="website">

      {/* NAV */}

      <nav className="nav">
        <div className="logo"><b>DELL</b> <small>Technologies</small></div>
        <a href="#hero">Inspiron</a>
      </nav>


      {/* SECTION 1 */}

      <section className="hero" id="hero">

        <video
          ref={video}
          className="heroVideo"
          autoPlay
          muted
          loop
          playsInline
          poster={heroImg}
          onPlay={() => setPlaying(true)}
          onPause={() => setPlaying(false)}
        >
          <source src={heroVideo} type="video/mp4" />
        </video>

        <div className="heroShade"></div>

        <div className="heroText">

          <h1>Dell Inspiron</h1>
          <p>14 Plus 2-in-1 Laptop</p>

          <button
            className={`play ${playing ? "isPlaying" : ""}`}
            onClick={videoPlay}
            aria-label={playing ? "Pause video" : "Play video"}
          >

            {playing ? (
              <span className="pauseIcon">
                <i></i>
                <i></i>
              </span>
            ) : (
              <span className="playIcon"></span>
            )}

          </button>

        </div>

        <Price />

        <div className="down">↓</div>

        <p className="copy">Copyright © 2025 Dell Inc.</p>
        <p className="terms">*T&Cs apply</p>

      </section>


      {/* SECTION 2 */}

      <section className="features">

        <button className="arrow left" onClick={prevF}>‹</button>

        <div className="cards">

          {features.map((x, i) => {

            let pos = "hide";

            if (i === fi) pos = "active";
            else if (i === (fi - 1 + features.length) % features.length) pos = "prev";
            else if (i === (fi + 1) % features.length) pos = "next";

            return (
              <div
                key={i}
                className={`card ${pos} ${zoom === i ? "zoom" : ""}`}
                onClick={() => cardClick(i)}
              >

                <div
                  className="cardImg"
                  style={{ backgroundImage: `url(${x.img})` }}
                ></div>

                <div className="cardShade"></div>

                <div className="cardText">

                  <span className="icon">{x.icon}</span>

                  <h2>{x.title}</h2>

                  <div className="line"></div>

                  <p>{x.text}</p>

                  {i === fi &&
                    <small className="explore">
                      {zoom === i ? "CLICK TO CLOSE" : "CLICK TO EXPLORE"}
                    </small>
                  }

                </div>

              </div>
            )

          })}

        </div>

        <button className="arrow right" onClick={nextF}>›</button>

        <Price />

        <p className="copy">Copyright © 2025 Dell Inc.</p>
        <p className="terms">*T&Cs apply</p>

      </section>


      {/* SECTION 3 */}

      <section className={`products ${p.type === "offer" ? "light" : ""}`}>

        <button className="arrow left" onClick={prevP}>‹</button>

        <div key={pi} className={`product ${dir === "right" ? "fromRight" : "fromLeft"}`}>

          <div className="productImg">
            <img src={p.img} alt={p.title} />
          </div>

          <div className="productText">

            <h2>{p.title}</h2>

            <div className="productLine"></div>

            <p>{p.sub}</p>

            {p.model && <h3>{p.model}</h3>}

            <div className="productPrice">
              {p.price}
            </div>

            {p.emi && <p className="emi">{p.emi}</p>}

            {p.type === "xps" &&
              <button className="know">KNOW MORE</button>
            }

          </div>

        </div>

        <button className="arrow right" onClick={nextP}>›</button>


        {/* slider dots */}

        <div className="dots">
          {products.map((x, i) =>
            <span
              key={i}
              className={i === pi ? "dot selected" : "dot"}
              onClick={() => {
                setDir(i > pi ? "right" : "left");
                setPi(i);
              }}
            ></span>
          )}
        </div>

        <p className="copy">Copyright © 2025 Dell Inc.</p>
        <p className="terms">*T&Cs apply</p>

      </section>

    </div>
  )
}


// price circle

function Price() {
  return (
    <div className="price">
      <small>Price</small>
      <span>Starting from</span>
      <b>₹56000*</b>
    </div>
  )
}

export default App;