#!/usr/bin/env python3
"""Adds About nav link + homepage About preview section"""
import os, re

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def patch_file(path, marker, old, new, label):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if marker in content:
        print(f"  ⏭️  Already patched: {label}")
        return
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {label}")

# ── Find homepage template ────────────────────────────────────────
candidates = [
    "app/templates/customer/index.html",
    "app/templates/customer/shop.html",
    "app/templates/index.html",
    "app/templates/base.html",
]
homepage = None
for c in candidates:
    p = os.path.join(BASE, c)
    if os.path.exists(p):
        homepage = p
        print(f"  📄 Found homepage: {c}")
        break

if not homepage:
    # List all html files to help debug
    print("  ⚠️  Could not find homepage. Listing all HTML files:")
    for root, dirs, files in os.walk(os.path.join(BASE, "app/templates")):
        for f in files:
            if f.endswith('.html'):
                print(f"     {os.path.join(root,f)}")
    exit(1)

with open(homepage, 'r', encoding='utf-8') as f:
    content = f.read()

# ── 1. Add "About" to navbar ─────────────────────────────────────
# Try common navbar patterns
nav_patterns = [
    ('<a href="/shop"', '<a href="/about">About Us</a>\n    <a href="/shop"'),
    ('<a href="{{ url_for(\'customer.index\') }}"', '<a href="/about">About Us</a>\n    <a href="{{ url_for(\'customer.index\') }}"'),
    ('</nav>', '  <a href="/about" style="color:inherit;text-decoration:none;font-weight:500;margin-right:1rem">About Us</a>\n</nav>'),
]

nav_added = False
for old, new in nav_patterns:
    if old in content and 'href="/about"' not in content:
        content = content.replace(old, new, 1)
        nav_added = True
        print("  ✅ About link added to navbar")
        break

if not nav_added and 'href="/about"' not in content:
    print("  ⚠️  Could not auto-patch navbar — will add floating button instead")

# ── 2. Add About preview section before </body> ───────────────────
about_section = """
<!-- ══ ABOUT PREVIEW SECTION ══════════════════════════════════ -->
<section id="about-preview" style="
  background: linear-gradient(160deg, #7B1C2E 0%, #560D1E 50%, #3D0A15 100%);
  padding: 5rem 1.5rem; position: relative; overflow: hidden;
">
  <!-- decorative circles -->
  <div style="position:absolute;top:-80px;right:-80px;width:350px;height:350px;border-radius:50%;background:radial-gradient(circle,rgba(201,150,62,.12),transparent 65%);pointer-events:none"></div>
  <div style="position:absolute;bottom:-60px;left:-60px;width:280px;height:280px;border-radius:50%;background:radial-gradient(circle,rgba(201,150,62,.07),transparent 65%);pointer-events:none"></div>

  <div style="max-width:1100px;margin:0 auto;position:relative;z-index:1">

    <!-- Tag -->
    <div style="display:flex;align-items:center;justify-content:center;gap:.7rem;margin-bottom:.8rem">
      <span style="width:40px;height:1px;background:rgba(201,150,62,.5)"></span>
      <span style="font-size:.68rem;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#C9963E">Our Story</span>
      <span style="width:40px;height:1px;background:rgba(201,150,62,.5)"></span>
    </div>

    <!-- Headline -->
    <h2 style="
      font-family:'Playfair Display',Georgia,serif;
      font-size:clamp(2rem,5vw,3.2rem);font-weight:900;
      color:#fff;text-align:center;line-height:1.15;margin-bottom:1rem;
    ">
      30 Years of Trust,<br><em style="color:#E8B96A;font-style:italic">One Family's Promise</em>
    </h2>

    <p style="font-family:Georgia,serif;font-size:1.1rem;color:rgba(255,255,255,.7);text-align:center;max-width:620px;margin:0 auto 3rem;line-height:1.75">
      From a humble cloth shop opposite the Mantha Bus Stand to Maharashtra's most loved fashion destination — M.B Maniyar has dressed generations of families with quality, care, and tradition.
    </p>

    <!-- 3 pillars -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1.2rem;margin-bottom:3rem">
      {% for icon, title, desc in [
        ('🏅', 'Uncompromising Quality', '30 years of handpicking every fabric. If it is not good enough for our family, it is not good enough for yours.'),
        ('🤝', 'Community First', 'Mantha gave us everything. We pour that gratitude back through fair prices and honest advice — every single day.'),
        ('🌐', 'Now Online', 'The same warmth and quality you trust in-store, now delivered to your doorstep anywhere in India.'),
      ] %}
      <div style="background:rgba(255,255,255,.06);border:1px solid rgba(201,150,62,.18);border-radius:20px;padding:1.8rem 1.4rem;text-align:center;transition:transform .3s,background .3s"
           onmouseover="this.style.transform='translateY(-5px)';this.style.background='rgba(201,150,62,.1)'"
           onmouseout="this.style.transform='';this.style.background='rgba(255,255,255,.06)'">
        <div style="font-size:2.2rem;margin-bottom:.7rem">{{ icon }}</div>
        <div style="font-family:'Playfair Display',Georgia,serif;font-size:1.1rem;font-weight:700;color:#E8B96A;margin-bottom:.5rem">{{ title }}</div>
        <div style="font-size:.84rem;color:rgba(255,255,255,.6);line-height:1.65">{{ desc }}</div>
      </div>
      {% endfor %}
    </div>

    <!-- Founder quote strip -->
    <div style="background:rgba(201,150,62,.08);border:1px solid rgba(201,150,62,.2);border-radius:16px;padding:1.5rem 2rem;max-width:700px;margin:0 auto 2.5rem;display:flex;align-items:flex-start;gap:1.2rem">
      <div style="font-family:Georgia,serif;font-size:3.5rem;color:#C9963E;line-height:.6;flex-shrink:0;margin-top:.2rem">"</div>
      <div>
        <p style="font-family:Georgia,serif;font-style:italic;font-size:1rem;color:rgba(255,255,255,.82);line-height:1.7;margin-bottom:.7rem">
          Every person who walks through our door is a guest in our home. We have built this store on one belief — give people quality they can trust, and treat every customer with the warmth they deserve.
        </p>
        <div style="display:flex;align-items:center;gap:.8rem">
          <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#C9963E,#E8B96A);display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-weight:700;color:#560D1E;font-size:.9rem">P</div>
          <div>
            <div style="font-weight:700;color:#E8B96A;font-size:.88rem">Pawan Maniyar</div>
            <div style="font-size:.72rem;color:rgba(255,255,255,.4);letter-spacing:1px">Founder · M.B Maniyar Cloth Store</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats row -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;max-width:700px;margin:0 auto 3rem;text-align:center">
      {% for num, lbl in [('30+','Years'),('5000+','Families'),('1000+','Styles'),('1','Promise')] %}
      <div>
        <div style="font-family:'Playfair Display',Georgia,serif;font-size:clamp(1.6rem,4vw,2.4rem);font-weight:900;color:#E8B96A;line-height:1">{{ num }}</div>
        <div style="font-size:.72rem;text-transform:uppercase;letter-spacing:1.5px;color:rgba(255,255,255,.4);margin-top:.2rem">{{ lbl }}</div>
      </div>
      {% endfor %}
    </div>

    <!-- CTA buttons -->
    <div style="text-align:center;display:flex;gap:1rem;justify-content:center;flex-wrap:wrap">
      <a href="/about" style="display:inline-flex;align-items:center;gap:.5rem;background:linear-gradient(135deg,#C9963E,#E8B96A);color:#560D1E;border-radius:50px;padding:.75rem 2rem;font-weight:700;font-size:.9rem;text-decoration:none;transition:transform .2s,box-shadow .2s"
         onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 10px 30px rgba(201,150,62,.35)'"
         onmouseout="this.style.transform='';this.style.boxShadow=''">
        📖 Read Our Full Story
      </a>
      <a href="tel:9421474678" style="display:inline-flex;align-items:center;gap:.5rem;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);color:#fff;border-radius:50px;padding:.75rem 2rem;font-weight:600;font-size:.9rem;text-decoration:none;transition:all .2s"
         onmouseover="this.style.background='rgba(255,255,255,.14)'"
         onmouseout="this.style.background='rgba(255,255,255,.08)'">
        📞 Call +91 94214 74678
      </a>
    </div>

  </div>
</section>
<!-- ══ END ABOUT PREVIEW ═════════════════════════════════════════ -->

"""

if 'about-preview' not in content:
    content = content.replace('</body>', about_section + '</body>')
    print("  ✅ About preview section injected before </body>")
else:
    print("  ⏭️  About section already present")

# ── If no nav link was added, add a floating "About" button ──────
if not nav_added and 'href="/about"' not in content:
    floating_btn = """
<a href="/about" style="
  position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;
  background:linear-gradient(135deg,#7B1C2E,#9E2A3F);
  color:#E8B96A;border-radius:50px;padding:.6rem 1.2rem;
  font-weight:700;font-size:.82rem;text-decoration:none;
  box-shadow:0 4px 20px rgba(123,28,46,.4);
  display:flex;align-items:center;gap:.5rem;
  transition:transform .2s;
" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform=''">
  ✨ About Us
</a>
"""
    content = content.replace('</body>', floating_btn + '</body>')
    print("  ✅ Floating About button added (fallback)")

with open(homepage, 'w', encoding='utf-8') as f:
    f.write(content)

print()
print("="*55)
print("  🎉 Done! Visit: http://localhost:5000/shop")
print("  About page:    http://localhost:5000/about")
print("="*55)
