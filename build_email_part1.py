#!/usr/bin/env python3
"""
📧 MBM Email & Password System - Part 1
- Email verification on register
- Order confirmation emails
- Password reset via email
- Change password (all users + admin)
Run: python3 build_email_part1.py
"""
import os, subprocess

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {path}")

def append_if_missing(path, marker, content):
    with open(path, 'r') as f:
        existing = f.read()
    if marker not in existing:
        with open(path, 'a') as f:
            f.write(content)
        print(f"  ✅ Patched {os.path.basename(path)}")
    else:
        print(f"  ⏭️  Already in {os.path.basename(path)}")

print("\n📧 Building Email + Password System\n" + "="*45)

# ══════════════════════════════════════════════
# 1. Install Flask-Mail
# ══════════════════════════════════════════════
print("\n📦 Installing Flask-Mail...")
try:
    subprocess.run(["pip", "install", "Flask-Mail", "--break-system-packages", "-q"], check=True)
    print("  ✅ Flask-Mail installed")
except:
    subprocess.run(["pip", "install", "Flask-Mail", "-q"])
    print("  ✅ Flask-Mail installed")

# ══════════════════════════════════════════════
# 2. Update config.py with mail settings
# ══════════════════════════════════════════════
print("\n⚙️  Updating config.py...")
w("app/config.py", """import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Core
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'mbm-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mbmaniyar.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Store
    STORE_NAME    = os.environ.get('STORE_NAME', 'M.B Maniyar Cloth Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', 'Main Road, Opposite Bus Stand, Mantha, Jalna')
    STORE_PHONE   = os.environ.get('STORE_PHONE', '+91 94214 74678')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Mail (Gmail SMTP)
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')   # your Gmail
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')   # Gmail App Password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'M.B Maniyar <noreply@mbmaniyar.com>')
    MAIL_ENABLED  = bool(os.environ.get('MAIL_USERNAME', ''))
""")

# ══════════════════════════════════════════════
# 3. Patch models.py — add email verification tokens + password reset
# ══════════════════════════════════════════════
print("\n🗄️  Patching models.py...")
models_path = os.path.join(BASE, "app/models.py")
with open(models_path, 'r') as f:
    models = f.read()

# Add email_verified + reset token fields to User model
if 'email_verified' not in models:
    models = models.replace(
        "is_active_account = db.Column(db.Boolean, default=True)",
        """is_active_account   = db.Column(db.Boolean, default=True)
    email_verified      = db.Column(db.Boolean, default=False)
    verification_token  = db.Column(db.String(100), unique=True)
    reset_token         = db.Column(db.String(100), unique=True)
    reset_token_expiry  = db.Column(db.DateTime)"""
    )
    with open(models_path, 'w') as f:
        f.write(models)
    print("  ✅ User model updated with email/reset fields")
else:
    print("  ⏭️  Already patched")

# ══════════════════════════════════════════════
# 4. Create mail service
# ══════════════════════════════════════════════
print("\n📬 Creating mail service...")
w("app/mail_service.py", r"""
from flask import current_app, render_template_string
from flask_mail import Message

def get_mail():
    from app import mail
    return mail

# ── BASE EMAIL TEMPLATE ───────────────────────────────────────────
def base_html(title, content, cta_text=None, cta_url=None):
    cta_block = ""
    if cta_text and cta_url:
        cta_block = f"""
        <div style="text-align:center;margin:2rem 0">
          <a href="{cta_url}" style="display:inline-block;background:linear-gradient(135deg,#7B1C2E,#9E2A3F);
             color:#E8B96A;text-decoration:none;padding:.85rem 2.5rem;border-radius:50px;
             font-weight:700;font-size:.95rem;letter-spacing:.5px">{cta_text}</a>
        </div>"""
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
</head>
<body style="margin:0;padding:0;background:#F5F0EB;font-family:'Outfit',Arial,sans-serif">
<div style="max-width:600px;margin:2rem auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 30px rgba(0,0,0,.08)">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#560D1E,#7B1C2E);padding:2rem;text-align:center">
    <div style="font-size:1.5rem;font-weight:800;color:#E8B96A;letter-spacing:.5px">M.B Maniyar</div>
    <div style="font-size:.75rem;color:rgba(255,255,255,.5);letter-spacing:2px;text-transform:uppercase;margin-top:.3rem">Cloth Store · Mantha</div>
  </div>

  <!-- Body -->
  <div style="padding:2.5rem 2rem">
    <h2 style="font-size:1.3rem;font-weight:800;color:#560D1E;margin-bottom:1rem">{title}</h2>
    {content}
    {cta_block}
  </div>

  <!-- Footer -->
  <div style="background:#F5F0EB;padding:1.2rem 2rem;text-align:center;border-top:1px solid #E8DDD4">
    <p style="font-size:.78rem;color:#9A8578;margin:0">
      Main Road, Opposite Bus Stand, Mantha, Jalna · <a href="tel:9421474678" style="color:#7B1C2E">+91 94214 74678</a>
    </p>
    <p style="font-size:.72rem;color:#BEB0A6;margin:.4rem 0 0">© 2025 M.B Maniyar Cloth Store. All rights reserved.</p>
  </div>
</div>
</body></html>"""

def send_email(to, subject, html_body):
    """Send email — silently fails if mail not configured."""
    try:
        if not current_app.config.get('MAIL_ENABLED'):
            print(f"  [MAIL DISABLED] Would send to {to}: {subject}")
            return True
        mail = get_mail()
        msg  = Message(subject=subject, recipients=[to], html=html_body,
                       sender=current_app.config['MAIL_DEFAULT_SENDER'])
        mail.send(msg)
        return True
    except Exception as e:
        print(f"  [MAIL ERROR] {e}")
        return False

# ── VERIFICATION EMAIL ────────────────────────────────────────────
def send_verification_email(user, token):
    from flask import url_for
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    content = f"""
    <p style="color:#5A4A42;line-height:1.7;margin-bottom:1rem">
      Hi <strong>{user.full_name}</strong>, welcome to M.B Maniyar! 🎉
    </p>
    <p style="color:#5A4A42;line-height:1.7;margin-bottom:1rem">
      Please verify your email address to activate your account and start shopping.
    </p>
    <div style="background:#FDF3E3;border:1px solid #E8C97A;border-radius:10px;padding:1rem;margin:1rem 0;text-align:center">
      <div style="font-size:.78rem;color:#9A7040;text-transform:uppercase;letter-spacing:1px;margin-bottom:.4rem">Verification Link</div>
      <a href="{verify_url}" style="color:#7B1C2E;font-size:.82rem;word-break:break-all">{verify_url}</a>
    </div>
    <p style="color:#9A8578;font-size:.82rem">This link expires in 24 hours. If you didn't register, ignore this email.</p>
    """
    return send_email(user.email, "✅ Verify Your Email — M.B Maniyar",
                      base_html("Verify Your Email Address", content,
                                "Verify My Email", verify_url))

# ── ORDER CONFIRMATION ────────────────────────────────────────────
def send_order_confirmation(user, order):
    items_html = ""
    for item in order.items:
        items_html += f"""
        <tr>
          <td style="padding:.6rem .8rem;font-size:.88rem;color:#3D2B22">{item.product.name} ({item.variant.size if item.variant else ''})</td>
          <td style="padding:.6rem .8rem;text-align:center;font-size:.88rem">{item.quantity}</td>
          <td style="padding:.6rem .8rem;text-align:right;font-size:.88rem;font-weight:600">₹{item.total_price:.0f}</td>
        </tr>"""
    content = f"""
    <p style="color:#5A4A42;line-height:1.7">
      Hi <strong>{user.full_name}</strong>, your order has been placed successfully! 🛍️
    </p>
    <div style="background:#FDF3E3;border-radius:10px;padding:1rem 1.2rem;margin:1.2rem 0;display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-size:.72rem;color:#9A7040;text-transform:uppercase;letter-spacing:1px">Order Number</div>
        <div style="font-size:1.1rem;font-weight:800;color:#560D1E;font-family:monospace">{order.order_number}</div>
      </div>
      <div style="text-align:right">
        <div style="font-size:.72rem;color:#9A7040;text-transform:uppercase;letter-spacing:1px">Status</div>
        <div style="font-size:.9rem;font-weight:700;color:#166534;background:#D1FAE5;padding:.2rem .7rem;border-radius:50px">{order.status.title()}</div>
      </div>
    </div>
    <table style="width:100%;border-collapse:collapse;margin:1rem 0">
      <thead>
        <tr style="background:#F5F0EB">
          <th style="padding:.6rem .8rem;text-align:left;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;color:#9A8578">Item</th>
          <th style="padding:.6rem .8rem;text-align:center;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;color:#9A8578">Qty</th>
          <th style="padding:.6rem .8rem;text-align:right;font-size:.75rem;text-transform:uppercase;letter-spacing:1px;color:#9A8578">Price</th>
        </tr>
      </thead>
      <tbody>{items_html}</tbody>
      <tfoot>
        <tr style="border-top:2px solid #E8DDD4">
          <td colspan="2" style="padding:.7rem .8rem;font-weight:700;color:#560D1E">Total</td>
          <td style="padding:.7rem .8rem;text-align:right;font-weight:800;font-size:1.05rem;color:#560D1E">₹{order.total_amount:.0f}</td>
        </tr>
      </tfoot>
    </table>
    <p style="color:#9A8578;font-size:.82rem;line-height:1.6">
      Payment: <strong>{order.payment_method.upper()}</strong> ·
      We'll notify you when your order ships. Questions? Call us at <strong>+91 94214 74678</strong>.
    </p>
    """
    return send_email(user.email, f"🛍️ Order Confirmed #{order.order_number} — M.B Maniyar",
                      base_html("Your Order is Confirmed!", content))

# ── ORDER STATUS UPDATE ───────────────────────────────────────────
def send_order_status_update(user, order):
    status_info = {
        'confirmed':  ('✅', 'Order Confirmed',   'Your order is confirmed and being prepared.', '#166534', '#D1FAE5'),
        'processing': ('⚙️', 'Being Processed',   'Your order is being packed with care.', '#92400E', '#FEF3C7'),
        'shipped':    ('🚚', 'Out for Delivery',  'Your order is on its way to you!', '#1E40AF', '#DBEAFE'),
        'delivered':  ('🎉', 'Delivered!',         'Your order has been delivered. Enjoy!', '#166534', '#D1FAE5'),
        'cancelled':  ('❌', 'Order Cancelled',   'Your order has been cancelled.', '#991B1B', '#FEE2E2'),
    }
    emoji, title, msg, txt_col, bg_col = status_info.get(order.status,
        ('📦', order.status.title(), 'Your order status has been updated.', '#1A2340', '#EFF6FF'))
    content = f"""
    <p style="color:#5A4A42;line-height:1.7">Hi <strong>{user.full_name}</strong>,</p>
    <div style="background:{bg_col};border-radius:12px;padding:1.2rem;margin:1.2rem 0;text-align:center">
      <div style="font-size:2.5rem;margin-bottom:.5rem">{emoji}</div>
      <div style="font-size:1.1rem;font-weight:800;color:{txt_col}">{title}</div>
      <div style="font-size:.88rem;color:{txt_col};opacity:.8;margin-top:.3rem">{msg}</div>
    </div>
    <div style="background:#F5F0EB;border-radius:10px;padding:.8rem 1rem;margin:1rem 0">
      <span style="font-size:.8rem;color:#9A8578">Order: </span>
      <strong style="font-family:monospace;color:#560D1E">{order.order_number}</strong>
      <span style="float:right;font-size:.8rem;font-weight:700;color:#560D1E">₹{order.total_amount:.0f}</span>
    </div>
    <p style="color:#9A8578;font-size:.82rem">Questions? Call <strong>+91 94214 74678</strong> or reply to this email.</p>
    """
    return send_email(user.email, f"{emoji} Order Update — {order.order_number}",
                      base_html(f"Order Update: {title}", content))

# ── PASSWORD RESET EMAIL ──────────────────────────────────────────
def send_password_reset_email(user, token):
    from flask import url_for
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    content = f"""
    <p style="color:#5A4A42;line-height:1.7">
      Hi <strong>{user.full_name}</strong>, we received a request to reset your password.
    </p>
    <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:1rem;margin:1rem 0;text-align:center">
      <div style="font-size:.78rem;color:#991B1B;text-transform:uppercase;letter-spacing:1px;margin-bottom:.4rem">Reset Link (expires in 1 hour)</div>
      <a href="{reset_url}" style="color:#7B1C2E;font-size:.82rem;word-break:break-all">{reset_url}</a>
    </div>
    <p style="color:#9A8578;font-size:.82rem">If you didn't request this, your account is safe — just ignore this email.</p>
    """
    return send_email(user.email, "🔐 Reset Your Password — M.B Maniyar",
                      base_html("Password Reset Request", content,
                                "Reset My Password", reset_url))

# ── WELCOME EMAIL (after verify) ──────────────────────────────────
def send_welcome_email(user):
    content = f"""
    <p style="color:#5A4A42;line-height:1.7;font-size:1.05rem">
      Welcome to the M.B Maniyar family, <strong>{user.full_name}</strong>! 🎉
    </p>
    <p style="color:#5A4A42;line-height:1.7">
      Your account is now verified. You can now shop our full collection of premium garments,
      track your orders, and enjoy exclusive deals.
    </p>
    <div style="background:#FDF3E3;border-radius:12px;padding:1.2rem;margin:1.2rem 0">
      <div style="font-size:.78rem;color:#9A7040;text-transform:uppercase;letter-spacing:1px;margin-bottom:.8rem">What's waiting for you</div>
      {''.join(f'<div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.5rem"><span>{e}</span><span style="font-size:.88rem;color:#5A4A42">{t}</span></div>'
               for e,t in [('🤵','Premium Suits & Formals'),('👕','Readymade Garments'),('🧒',"Kids' Apparel"),('🌙','Nightwear & Innerwear')])}
    </div>
    <p style="color:#9A8578;font-size:.82rem">Visit us at Main Road, Opposite Bus Stand, Mantha or shop online anytime.</p>
    """
    return send_email(user.email, "🎉 Welcome to M.B Maniyar Cloth Store!",
                      base_html("You're in the Family!", content, "Start Shopping", "/shop"))
""")

# ══════════════════════════════════════════════
# 5. Patch __init__.py to initialize Flask-Mail
# ══════════════════════════════════════════════
print("\n🔧 Patching app/__init__.py...")
init_path = os.path.join(BASE, "app/__init__.py")
with open(init_path, 'r') as f:
    init_content = f.read()

if 'Flask-Mail' not in init_content and 'flask_mail' not in init_content:
    init_content = init_content.replace(
        'from flask import Flask',
        'from flask import Flask\nfrom flask_mail import Mail\n\nmail = Mail()'
    )
    init_content = init_content.replace(
        'db.init_app(app)',
        'db.init_app(app)\n    mail.init_app(app)'
    )
    with open(init_path, 'w') as f:
        f.write(init_content)
    print("  ✅ Flask-Mail initialized in app")
else:
    print("  ⏭️  Flask-Mail already in __init__.py")

# ══════════════════════════════════════════════
# 6. Update requirements.txt
# ══════════════════════════════════════════════
print("\n📦 Updating requirements.txt...")
req_path = os.path.join(BASE, "requirements.txt")
with open(req_path, 'r') as f:
    reqs = f.read()
if 'Flask-Mail' not in reqs:
    with open(req_path, 'a') as f:
        f.write('\nFlask-Mail>=0.9.1\n')
    print("  ✅ Flask-Mail added to requirements.txt")

# ══════════════════════════════════════════════
# 7. .env update instructions
# ══════════════════════════════════════════════
print("\n📝 Creating .env.example...")
w(".env.example", """# Copy this to .env and fill in your values
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///mbmaniyar.db
STORE_NAME=M.B Maniyar Cloth Store
STORE_ADDRESS=Main Road, Opposite Bus Stand, Mantha, Jalna
STORE_PHONE=+91 94214 74678

# Gmail SMTP Settings
# 1. Enable 2FA on your Gmail
# 2. Go to Google Account > Security > App Passwords
# 3. Generate password for "Mail"
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
MAIL_DEFAULT_SENDER=M.B Maniyar <your-gmail@gmail.com>
""")

print("""
╔══════════════════════════════════════════════╗
║  ✅ Part 1 Complete!                         ║
║  Now run: python3 build_email_part2.py       ║
╚══════════════════════════════════════════════╝
""")
