#!/usr/bin/env python3
"""Builds the About Us page into the MBM Flask app"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

# ── ABOUT PAGE TEMPLATE ───────────────────────────────────────────
w("app/templates/customer/about.html", r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>About Us | M.B Maniyar Cloth Store</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=DM+Sans:wght@300;400;500;600&family=Playfair+Display:ital,wght@0,700;0,900;1,700&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
<style>
:root {
  --maroon: #7B1C2E;
  --maroon-deep: #560D1E;
  --maroon-light: #9E2A3F;
  --gold: #C9963E;
  --gold-light: #E8B96A;
  --gold-pale: #FDF3E3;
  --cream: #FAF6F0;
  --cream-dark: #F0E9DC;
  --text: #2C1810;
  --muted: #7A6358;
  --white: #FFFFFF;
  --ff-display: 'Playfair Display', serif;
  --ff-serif: 'Cormorant Garamond', serif;
  --ff-sans: 'DM Sans', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--ff-sans); background: var(--cream); color: var(--text); overflow-x: hidden; }

/* ── NAVBAR ── */
.mbm-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 999;
  background: rgba(123,28,46,.97); backdrop-filter: blur(12px);
  padding: .9rem 2rem;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid rgba(201,150,62,.25);
}
.nav-brand {
  font-family: var(--ff-display); font-size: 1.3rem; font-weight: 700;
  color: var(--gold-light); text-decoration: none; letter-spacing: .5px;
}
.nav-links { display: flex; gap: 1.6rem; }
.nav-links a {
  color: rgba(255,255,255,.75); text-decoration: none; font-size: .85rem;
  font-weight: 500; letter-spacing: .5px; transition: color .2s;
}
.nav-links a:hover { color: var(--gold-light); }

/* ── HERO ── */
.hero {
  min-height: 100vh;
  background:
    linear-gradient(160deg, rgba(86,13,30,.92) 0%, rgba(123,28,46,.85) 45%, rgba(86,13,30,.96) 100%),
    repeating-linear-gradient(45deg, transparent, transparent 20px, rgba(201,150,62,.03) 20px, rgba(201,150,62,.03) 21px),
    repeating-linear-gradient(-45deg, transparent, transparent 20px, rgba(201,150,62,.03) 20px, rgba(201,150,62,.03) 21px);
  display: flex; align-items: center; justify-content: center;
  text-align: center; position: relative; padding: 8rem 2rem 5rem;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute; inset: 0;
  background: radial-gradient(ellipse 80% 60% at 50% 60%, rgba(201,150,62,.08) 0%, transparent 70%);
  pointer-events: none;
}
.hero-ornament {
  font-size: 1.1rem; color: var(--gold); letter-spacing: 4px;
  text-transform: uppercase; margin-bottom: 1.5rem;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
  opacity: 0; animation: fadeUp .8s .2s ease forwards;
}
.hero-ornament::before, .hero-ornament::after {
  content: ''; width: 60px; height: 1px; background: var(--gold); opacity: .5;
}
.hero-headline {
  font-family: var(--ff-display);
  font-size: clamp(3rem, 8vw, 6.5rem);
  font-weight: 900; line-height: 1.05;
  color: var(--white);
  margin-bottom: 1rem;
  opacity: 0; animation: fadeUp .8s .35s ease forwards;
}
.hero-headline em { color: var(--gold-light); font-style: italic; }
.hero-sub {
  font-family: var(--ff-serif); font-size: clamp(1.1rem, 2.5vw, 1.5rem);
  color: rgba(255,255,255,.75); font-weight: 400; letter-spacing: .3px;
  max-width: 560px; margin: 0 auto 2.5rem; line-height: 1.6;
  opacity: 0; animation: fadeUp .8s .5s ease forwards;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: .7rem;
  background: rgba(201,150,62,.15); border: 1px solid rgba(201,150,62,.3);
  border-radius: 50px; padding: .55rem 1.4rem;
  color: var(--gold-light); font-size: .82rem; font-weight: 600; letter-spacing: .5px;
  opacity: 0; animation: fadeUp .8s .65s ease forwards;
}
.hero-scroll-hint {
  position: absolute; bottom: 2rem; left: 50%; transform: translateX(-50%);
  color: rgba(255,255,255,.35); font-size: .78rem; letter-spacing: 1.5px;
  text-transform: uppercase; display: flex; flex-direction: column; align-items: center; gap: .5rem;
  animation: bob 2.5s ease-in-out infinite;
}
@keyframes bob { 0%,100%{transform:translateX(-50%) translateY(0)} 50%{transform:translateX(-50%) translateY(6px)} }

/* ── SECTION BASE ── */
.section { padding: 6rem 2rem; }
.section-inner { max-width: 1100px; margin: 0 auto; }
.section-tag {
  font-family: var(--ff-sans); font-size: .68rem; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase; color: var(--gold);
  display: flex; align-items: center; gap: .7rem; margin-bottom: .8rem;
}
.section-tag::after { content: ''; flex: 1; max-width: 60px; height: 1px; background: var(--gold); opacity: .4; }
.section-title {
  font-family: var(--ff-display); font-size: clamp(2rem, 4.5vw, 3rem);
  font-weight: 900; line-height: 1.15; margin-bottom: 1.4rem;
}

/* ── STORY ── */
.story-section { background: var(--cream); }
.story-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5rem; align-items: center; }
.story-number {
  font-family: var(--ff-display); font-size: clamp(6rem, 14vw, 11rem);
  font-weight: 900; line-height: 1;
  background: linear-gradient(180deg, var(--gold-light) 0%, rgba(201,150,62,.1) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: -.5rem;
}
.story-para {
  font-family: var(--ff-serif); font-size: 1.2rem; line-height: 1.85;
  color: var(--muted); margin-bottom: 1.3rem;
}
.story-para strong { color: var(--maroon); font-weight: 600; }
.story-badge-row { display: flex; gap: .8rem; flex-wrap: wrap; margin-top: 1.5rem; }
.s-badge {
  background: var(--cream-dark); border: 1px solid rgba(123,28,46,.12);
  border-radius: 50px; padding: .4rem 1rem; font-size: .8rem; font-weight: 600;
  color: var(--maroon); display: flex; align-items: center; gap: .4rem;
}

/* ── QUOTE / FOUNDER ── */
.founder-section {
  background: linear-gradient(135deg, var(--maroon-deep) 0%, var(--maroon) 60%, var(--maroon-deep) 100%);
  position: relative; overflow: hidden;
}
.founder-section::before {
  content: '\201C';
  position: absolute; top: -2rem; left: 3rem;
  font-family: var(--ff-display); font-size: 20rem; font-weight: 900;
  color: rgba(201,150,62,.06); line-height: 1; pointer-events: none;
}
.founder-section::after {
  content: '';
  position: absolute; inset: 0;
  background: repeating-linear-gradient(90deg, transparent, transparent 80px, rgba(201,150,62,.02) 80px, rgba(201,150,62,.02) 81px);
  pointer-events: none;
}
.founder-inner { max-width: 820px; margin: 0 auto; text-align: center; position: relative; z-index: 1; }
.quote-mark { font-family: var(--ff-display); font-size: 4rem; color: var(--gold); line-height: .5; margin-bottom: 1rem; }
.founder-quote {
  font-family: var(--ff-serif); font-style: italic;
  font-size: clamp(1.4rem, 3vw, 2rem); line-height: 1.65;
  color: rgba(255,255,255,.92); margin-bottom: 2rem;
}
.founder-sig {
  display: flex; align-items: center; justify-content: center; gap: 1.2rem;
}
.sig-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  display: flex; align-items: center; justify-content: center;
  font-family: var(--ff-display); font-size: 1.4rem; font-weight: 700; color: var(--maroon-deep);
  flex-shrink: 0; border: 2px solid rgba(201,150,62,.4);
}
.sig-name { font-family: var(--ff-display); font-size: 1.1rem; font-weight: 700; color: var(--gold-light); }
.sig-title { font-size: .78rem; color: rgba(255,255,255,.5); letter-spacing: 1px; margin-top: .15rem; }

/* ── OFFERINGS ── */
.offerings-section { background: var(--cream-dark); }
.offerings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1.2rem; margin-top: 3rem; }
.offer-card {
  background: var(--white); border-radius: 20px;
  border: 1px solid rgba(123,28,46,.08);
  padding: 2rem 1.5rem;
  transition: transform .3s, box-shadow .3s;
  position: relative; overflow: hidden;
}
.offer-card::before {
  content: '';
  position: absolute; bottom: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--maroon), var(--gold));
  transform: scaleX(0); transform-origin: left;
  transition: transform .3s;
}
.offer-card:hover { transform: translateY(-6px); box-shadow: 0 20px 50px rgba(123,28,46,.12); }
.offer-card:hover::before { transform: scaleX(1); }
.offer-icon { font-size: 2.2rem; margin-bottom: .8rem; }
.offer-name { font-family: var(--ff-display); font-size: 1.15rem; font-weight: 700; color: var(--maroon); margin-bottom: .4rem; }
.offer-desc { font-size: .83rem; color: var(--muted); line-height: 1.6; }

/* ── VALUES ── */
.values-section { background: var(--cream); }
.values-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin-top: 3rem; }
.value-card {
  text-align: center; padding: 2.5rem 1.5rem;
  border: 1.5px solid rgba(201,150,62,.2);
  border-radius: 24px; position: relative;
  background: linear-gradient(160deg, rgba(253,243,227,.5) 0%, rgba(255,255,255,.2) 100%);
  transition: border-color .3s, transform .3s;
}
.value-card:hover { border-color: var(--gold); transform: translateY(-4px); }
.value-number {
  position: absolute; top: -1.2rem; left: 50%; transform: translateX(-50%);
  background: linear-gradient(135deg, var(--maroon), var(--maroon-light));
  color: var(--gold-light); font-family: var(--ff-display); font-size: .75rem;
  font-weight: 700; border-radius: 50px; padding: .25rem .85rem;
  letter-spacing: 1px; white-space: nowrap;
}
.value-icon { font-size: 2.5rem; margin-bottom: .8rem; }
.value-title { font-family: var(--ff-display); font-size: 1.4rem; font-weight: 700; color: var(--maroon); margin-bottom: .5rem; }
.value-text { font-family: var(--ff-serif); font-size: 1.05rem; color: var(--muted); line-height: 1.6; }

/* ── VISIT US ── */
.visit-section {
  background: var(--maroon-deep);
  position: relative; overflow: hidden;
}
.visit-section::before {
  content: '';
  position: absolute; top: -50%; right: -10%;
  width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(201,150,62,.08) 0%, transparent 65%);
  pointer-events: none;
}
.visit-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; position: relative; z-index: 1; }
.visit-title { font-family: var(--ff-display); font-size: clamp(2rem, 4vw, 2.8rem); font-weight: 900; color: var(--white); line-height: 1.2; margin-bottom: 1rem; }
.visit-title em { color: var(--gold-light); font-style: italic; }
.visit-sub { font-family: var(--ff-serif); font-size: 1.15rem; color: rgba(255,255,255,.65); line-height: 1.7; margin-bottom: 2rem; }
.contact-card {
  background: rgba(255,255,255,.06); border: 1px solid rgba(201,150,62,.2);
  border-radius: 20px; padding: 1.4rem 1.6rem;
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 1rem; transition: background .2s, border-color .2s;
}
.contact-card:hover { background: rgba(201,150,62,.08); border-color: rgba(201,150,62,.4); }
.contact-icon {
  width: 46px; height: 46px; border-radius: 14px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; color: var(--maroon-deep);
}
.contact-lbl { font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: rgba(255,255,255,.4); margin-bottom: .2rem; }
.contact-val { font-size: .95rem; font-weight: 600; color: var(--white); }
.visit-map {
  background: rgba(255,255,255,.05); border: 1px solid rgba(201,150,62,.15);
  border-radius: 24px; overflow: hidden; position: relative;
  min-height: 320px; display: flex; align-items: center; justify-content: center;
}
.map-placeholder {
  text-align: center; color: rgba(255,255,255,.4); padding: 2rem;
}
.map-placeholder .map-icon { font-size: 3.5rem; margin-bottom: 1rem; display: block; }
.cta-btn {
  display: inline-flex; align-items: center; gap: .6rem;
  background: linear-gradient(135deg, var(--gold), var(--gold-light));
  color: var(--maroon-deep); border-radius: 50px; padding: .8rem 2rem;
  font-weight: 700; font-size: .9rem; text-decoration: none;
  transition: transform .2s, box-shadow .2s; margin-top: 1.5rem;
  border: none; cursor: pointer; letter-spacing: .5px;
}
.cta-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(201,150,62,.35); }

/* ── STATS BAR ── */
.stats-bar {
  background: linear-gradient(135deg, var(--maroon), var(--maroon-light));
  padding: 3rem 2rem;
}
.stats-inner { max-width: 900px; margin: 0 auto; display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; text-align: center; }
.stat-num { font-family: var(--ff-display); font-size: clamp(2rem,5vw,3rem); font-weight: 900; color: var(--gold-light); line-height: 1; }
.stat-lbl { font-size: .75rem; font-weight: 600; color: rgba(255,255,255,.55); letter-spacing: 1px; text-transform: uppercase; margin-top: .3rem; }

/* ── FOOTER ── */
.mbm-footer {
  background: #1A0A10; padding: 2rem;
  text-align: center; font-size: .82rem; color: rgba(255,255,255,.3);
  border-top: 1px solid rgba(201,150,62,.1);
}
.mbm-footer a { color: var(--gold); text-decoration: none; }

/* ── ANIMATIONS ── */
@keyframes fadeUp { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
.reveal { opacity: 0; transform: translateY(30px); transition: opacity .7s ease, transform .7s ease; }
.reveal.visible { opacity: 1; transform: translateY(0); }

/* ── DIVIDER ── */
.ornament-divider {
  text-align: center; padding: 1rem 0; color: var(--gold);
  font-size: 1rem; letter-spacing: 8px; opacity: .6;
}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .story-grid, .visit-grid { grid-template-columns: 1fr; gap: 2.5rem; }
  .values-grid { grid-template-columns: 1fr; }
  .stats-inner { grid-template-columns: repeat(2,1fr); }
  .nav-links { display: none; }
}
</style>
</head>
<body>

<!-- NAV -->
<nav class="mbm-nav">
  <a href="/" class="nav-brand">M.B Maniyar</a>
  <div class="nav-links">
    <a href="/">Home</a>
    <a href="/shop">Shop</a>
    <a href="/about">About</a>
    <a href="tel:9421474678">📞 Call Us</a>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div>
    <div class="hero-ornament">✦ &nbsp;Est. 1993&nbsp; ✦ &nbsp;Mantha, Maharashtra&nbsp; ✦</div>
    <h1 class="hero-headline">
      Dressed in<br><em>Legacy.</em>
    </h1>
    <p class="hero-sub">
      30 years of weaving trust, quality, and style into the heart of Marathwada — one family, one promise, one perfect fit.
    </p>
    <div class="hero-badge">
      <span>⭐</span> Mantha's Most Trusted Cloth Store Since 1993
    </div>
  </div>
  <div class="hero-scroll-hint">
    <span>Scroll</span>
    <i class="bi bi-chevron-down"></i>
  </div>
</section>

<!-- STATS BAR -->
<div class="stats-bar">
  <div class="stats-inner">
    <div><div class="stat-num">30+</div><div class="stat-lbl">Years of Legacy</div></div>
    <div><div class="stat-num">5000+</div><div class="stat-lbl">Happy Families</div></div>
    <div><div class="stat-num">1000+</div><div class="stat-lbl">Fabric Varieties</div></div>
    <div><div class="stat-num">1</div><div class="stat-lbl">Unbroken Promise</div></div>
  </div>
</div>

<!-- STORY -->
<section class="section story-section">
  <div class="section-inner story-grid">
    <div>
      <div class="story-number">30</div>
      <div class="section-tag">Our Journey</div>
      <h2 class="section-title" style="color:var(--maroon)">A Story Stitched<br>in Every Thread</h2>
    </div>
    <div>
      <p class="story-para">
        What began as a <strong>humble cloth shop on Main Road, Mantha</strong>, has blossomed over three decades into one of Marathwada's most beloved fashion destinations. Since the early 1990s, <strong>M.B Maniyar Cloth Store</strong> has stood opposite the Mantha Bus Stand — a landmark as reliable as the buses that pass by — serving generation after generation of families who trust us not just for fabric, but for the moments we help them dress for. Weddings, Eid celebrations, school uniforms, festival kurtas — we have been part of it all.
      </p>
      <p class="story-para">
        Today, led with quiet passion by <strong>Pawan Maniyar</strong>, we are taking that same warmth and trust onto a nationwide digital stage. Our new online platform is not just an e-commerce store — it is an extension of our showroom floor, where you can browse premium readymade garments, tailored suits, and children's wear from the comfort of your home, backed by the same <strong>30-year guarantee of quality</strong> that our Mantha customers have always known.
      </p>
      <div class="story-badge-row">
        <span class="s-badge">🏆 Community Trusted</span>
        <span class="s-badge">👨‍👩‍👧‍👦 Family Run</span>
        <span class="s-badge">📍 Mantha, Jalna</span>
        <span class="s-badge">✨ Online Now</span>
      </div>
    </div>
  </div>
</section>

<div class="ornament-divider">✦ ✦ ✦</div>

<!-- FOUNDER QUOTE -->
<section class="section founder-section">
  <div class="founder-inner">
    <div class="quote-mark">"</div>
    <p class="founder-quote">
      Every customer who walks through our door — or now, every visitor who lands on our page — is not just a sale. They are a guest in our home. We have built this store on one simple belief: give people fabric they can trust, and treat every person with the warmth they deserve. That has never changed, and it never will.
    </p>
    <div class="founder-sig">
      <div class="sig-avatar">P</div>
      <div>
        <div class="sig-name">Pawan Maniyar</div>
        <div class="sig-title">Founder &amp; Proprietor · M.B Maniyar Cloth Store</div>
      </div>
    </div>
  </div>
</section>

<!-- OFFERINGS -->
<section class="section offerings-section">
  <div class="section-inner">
    <div style="text-align:center;margin-bottom:.5rem">
      <div class="section-tag" style="justify-content:center">What We Offer</div>
      <h2 class="section-title" style="color:var(--maroon)">Your One-Stop<br>Fashion Destination</h2>
      <p style="font-family:var(--ff-serif);font-size:1.1rem;color:var(--muted);max-width:540px;margin:0 auto">From the finest suiting fabric to the cutest kids' wear — we have everything your family needs, under one roof.</p>
    </div>
    <div class="offerings-grid reveal">
      <div class="offer-card">
        <div class="offer-icon">🤵</div>
        <div class="offer-name">Premium Suits</div>
        <div class="offer-desc">Custom-tailored and readymade suits crafted from fine wool, linen, and poly-blend fabrics. Perfect for weddings, functions, and boardrooms.</div>
      </div>
      <div class="offer-card">
        <div class="offer-icon">👕</div>
        <div class="offer-name">Readymade Garments</div>
        <div class="offer-desc">A curated collection of shirts, trousers, kurtas, and co-ord sets from trusted brands — always fresh, always in season.</div>
      </div>
      <div class="offer-card">
        <div class="offer-icon">👔</div>
        <div class="offer-name">Menswear</div>
        <div class="offer-desc">From sharp formal wear to relaxed casuals — our menswear range covers every occasion the modern Indian man needs to dress for.</div>
      </div>
      <div class="offer-card">
        <div class="offer-icon">🌙</div>
        <div class="offer-name">Nightwear & Innerwear</div>
        <div class="offer-desc">Comfortable, breathable nightwear and premium cotton innerwear for the whole family. Because comfort at home matters just as much.</div>
      </div>
      <div class="offer-card">
        <div class="offer-icon">🧒</div>
        <div class="offer-name">Kids' Apparel</div>
        <div class="offer-desc">Bright, durable, and adorable clothing for boys and girls. School uniforms to festival outfits — dressed up for every stage of growing up.</div>
      </div>
      <div class="offer-card">
        <div class="offer-icon">🧵</div>
        <div class="offer-name">Fabric & Tailoring</div>
        <div class="offer-desc">Select from our premium fabric rolls and get stitched to a perfect, personalized fit by our in-house master tailors.</div>
      </div>
    </div>
  </div>
</section>

<!-- VALUES -->
<section class="section values-section">
  <div class="section-inner">
    <div style="text-align:center;margin-bottom:.5rem">
      <div class="section-tag" style="justify-content:center">What We Stand For</div>
      <h2 class="section-title" style="color:var(--maroon)">Our Core Values</h2>
    </div>
    <div class="values-grid reveal">
      <div class="value-card">
        <div class="value-number">Value 01</div>
        <div class="value-icon">🏅</div>
        <div class="value-title">Uncompromising Quality</div>
        <p class="value-text">Every piece of fabric and every garment in our store passes through hands that have spent 30 years learning what quality truly means. We never compromise — not for margin, not for convenience.</p>
      </div>
      <div class="value-card">
        <div class="value-number">Value 02</div>
        <div class="value-icon">🤝</div>
        <div class="value-title">Community First</div>
        <p class="value-text">We are not just a store — we are a neighbour. The Mantha community has given us everything, and we pour that gratitude back through fair pricing, honest advice, and a door that is always open.</p>
      </div>
      <div class="value-card">
        <div class="value-number">Value 03</div>
        <div class="value-icon">🌐</div>
        <div class="value-title">Tradition Meets Convenience</div>
        <p class="value-text">Shop with us in-store or online — the experience is seamless either way. We honor our roots while embracing the future, so that the next generation can access the same quality we've always delivered.</p>
      </div>
    </div>
  </div>
</section>

<!-- VISIT US -->
<section class="section visit-section">
  <div class="section-inner visit-grid">
    <div>
      <div class="section-tag" style="color:var(--gold-light)">Find Us</div>
      <h2 class="visit-title">Come See Us.<br>We'd <em>Love</em> to Help.</h2>
      <p class="visit-sub">
        Step into our store on Main Road, Mantha, and experience 30 years of textile expertise in person. Our team is always ready to help you find the perfect outfit — no appointment needed.
      </p>
      <div class="contact-card">
        <div class="contact-icon">📍</div>
        <div>
          <div class="contact-lbl">Our Address</div>
          <div class="contact-val">Main Road, Opposite Bus Stand<br>Mantha, Jalna District, Maharashtra</div>
        </div>
      </div>
      <div class="contact-card">
        <div class="contact-icon" style="font-size:1rem">📞</div>
        <div>
          <div class="contact-lbl">Call or WhatsApp</div>
          <div class="contact-val">
            <a href="tel:9421474678" style="color:#fff;text-decoration:none">+91 94214 74678</a>
          </div>
        </div>
      </div>
      <div class="contact-card">
        <div class="contact-icon" style="font-size:1rem">🕙</div>
        <div>
          <div class="contact-lbl">Store Hours</div>
          <div class="contact-val">Mon – Sat: 10:00 AM – 9:00 PM</div>
        </div>
      </div>
      <a href="tel:9421474678" class="cta-btn">
        <i class="bi bi-telephone-fill"></i> Call Us Now
      </a>
      <a href="/shop" class="cta-btn" style="margin-left:.8rem;background:rgba(255,255,255,.08);color:#fff;border:1px solid rgba(255,255,255,.2)">
        Shop Online →
      </a>
    </div>
    <div class="visit-map">
      <div class="map-placeholder">
        <span class="map-icon">🗺️</span>
        <div style="font-family:var(--ff-display);font-size:1.1rem;color:rgba(255,255,255,.6);margin-bottom:.5rem">M.B Maniyar Cloth Store</div>
        <div style="font-size:.82rem;color:rgba(255,255,255,.35)">Main Road, Opp. Bus Stand<br>Mantha, Maharashtra</div>
        <a href="https://maps.google.com?q=Mantha+Jalna+Maharashtra" target="_blank" class="cta-btn" style="margin-top:1.2rem;font-size:.82rem">
          <i class="bi bi-geo-alt-fill"></i> Open in Maps
        </a>
      </div>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="mbm-footer">
  <div style="margin-bottom:.5rem;font-family:var(--ff-display);font-size:1rem;color:rgba(255,255,255,.5)">M.B Maniyar Cloth Store</div>
  <div>Main Road, Opp. Bus Stand, Mantha, Jalna · <a href="tel:9421474678">+91 94214 74678</a></div>
  <div style="margin-top:.5rem;font-size:.75rem;color:rgba(255,255,255,.2)">© 2025 M.B Maniyar. Crafted with ♥ in Marathwada.</div>
</footer>

<script>
// Scroll reveal
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if(e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.15 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
</script>
</body>
</html>
""")

# Add route to customer blueprint
route_path = os.path.join(BASE, "app/customer/routes.py")
with open(route_path, 'r') as f:
    routes = f.read()

if "def about(" not in routes:
    routes += """

@customer_bp.route('/about')
def about():
    return render_template('customer/about.html')
"""
    with open(route_path, 'w') as f:
        f.write(routes)
    print("  ✅ /about route added to customer blueprint")
else:
    print("  ⏭️  /about route already exists")

print()
print("="*55)
print("  🎉 About page built!")
print("  Visit: http://localhost:5000/about")
print("="*55)
