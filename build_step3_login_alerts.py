#!/usr/bin/env python3
"""
BUILD STEP 3 - Login Security Alert Emails
Patches auth/routes.py to send a security email on every login.
Run: python3 build_step3_login_alerts.py
"""
import os

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ Written: {path}")

print("\n🔐 Building Login Security Alert System\n" + "="*45)

# ══════════════════════════════════════════════════════════════════
# 1. Create the security email service
# ══════════════════════════════════════════════════════════════════
print("\n📧 Creating security email service...")

w("app/security_emails.py", r"""
# security_emails.py
# PURPOSE : Send security-related emails (login alerts, password changes)
# These emails help users know if someone else is accessing their account

import os
from datetime import datetime
from flask import current_app


def get_device_info(request):
    """
    Extracts browser, OS, and IP info from the incoming HTTP request.
    This tells the user WHAT device was used to log in.
    """
    user_agent = request.headers.get('User-Agent', 'Unknown device')

    # ── Detect Browser ─────────────────────────────────────────────
    if 'Chrome' in user_agent and 'Edg' not in user_agent:
        browser = 'Google Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Mozilla Firefox'
    elif 'Safari' in user_agent and 'Chrome' not in user_agent:
        browser = 'Safari'
    elif 'Edg' in user_agent:
        browser = 'Microsoft Edge'
    elif 'Opera' in user_agent or 'OPR' in user_agent:
        browser = 'Opera'
    else:
        browser = 'Unknown Browser'

    # ── Detect Operating System ────────────────────────────────────
    if 'Windows NT 10' in user_agent:
        os_name = 'Windows 10/11'
    elif 'Windows' in user_agent:
        os_name = 'Windows'
    elif 'Android' in user_agent:
        os_name = 'Android'
    elif 'iPhone' in user_agent or 'iPad' in user_agent:
        os_name = 'iOS (iPhone/iPad)'
    elif 'Macintosh' in user_agent:
        os_name = 'macOS'
    elif 'Linux' in user_agent:
        os_name = 'Linux'
    else:
        os_name = 'Unknown OS'

    # ── Get IP Address ─────────────────────────────────────────────
    # X-Forwarded-For is set by proxies (like Render/Nginx)
    # We always check that first, then fall back to direct IP
    ip = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.headers.get('X-Real-IP', '')
        or request.remote_addr
        or 'Unknown IP'
    )

    return {
        'browser' : browser,
        'os'      : os_name,
        'ip'      : ip,
        'agent'   : user_agent[:80],   # truncate very long strings
    }


def send_login_alert(user, request):
    """
    Sends a login security alert email to the user.
    Called immediately after a successful login.

    If the user has no real email (walkin/employee auto-generated),
    we skip silently - no crash.
    """

    # Skip if no real email (auto-generated internal addresses)
    if not user.email or user.email.endswith('@mbmaniyar.local'):
        return

    # Skip if mail is not configured
    if not current_app.config.get('MAIL_ENABLED'):
        print(f"  [MAIL DISABLED] Skipping login alert for {user.email}")
        return

    try:
        from app import mail
        from flask_mail import Message

        # Collect device info from the HTTP request
        device = get_device_info(request)

        # Format the login time nicely
        # e.g. "Saturday, 14 March 2025 at 09:45 PM"
        login_time = datetime.now().strftime('%A, %d %B %Y at %I:%M %p')

        # ── Build the security alert email ────────────────────────
        msg = Message(
            subject    = f"🔐 New Login to Your M.B Maniyar Account",
            recipients = [user.email],
            # Plain text fallback
            body = f"""
Security Alert - New Login Detected

Hi {user.full_name},

A new login to your M.B Maniyar account was detected.

Login Details:
  Time     : {login_time}
  Browser  : {device['browser']}
  System   : {device['os']}
  IP Address: {device['ip']}

If this was you, no action is needed.

If you did NOT log in, your account may be compromised.
Please change your password immediately at:
  https://mbmaniyar.onrender.com/change-password

Or call us at +91 94214 74678.

- M.B Maniyar Security Team
            """.strip(),

            # Rich HTML version
            html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F0EB;
             font-family:'Helvetica Neue',Arial,sans-serif">
<div style="max-width:580px;margin:2rem auto;
            background:#fff;border-radius:16px;
            overflow:hidden;
            box-shadow:0 4px 30px rgba(0,0,0,0.08)">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#560D1E,#7B1C2E);
              padding:28px 32px">
    <div style="font-size:18px;font-weight:900;
                color:#E8B96A;letter-spacing:0.5px">
      M.B Maniyar
    </div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);
                letter-spacing:2px;text-transform:uppercase;
                margin-top:2px">
      Security Alert
    </div>
  </div>

  <!-- Body -->
  <div style="padding:28px 32px">

    <!-- Shield icon + title -->
    <div style="text-align:center;margin-bottom:20px">
      <div style="font-size:48px;margin-bottom:8px">🔐</div>
      <h2 style="font-size:20px;font-weight:700;
                 color:#2C1810;margin:0">
        New Login Detected
      </h2>
      <p style="color:#7A6358;font-size:14px;margin:6px 0 0">
        Hi <strong>{user.full_name}</strong>, someone just
        signed into your account.
      </p>
    </div>

    <!-- Login details card -->
    <div style="background:#FDF6EE;border-radius:12px;
                border:1px solid #E8DDD4;
                padding:20px 24px;margin:20px 0">

      <div style="font-size:10px;font-weight:700;
                  text-transform:uppercase;letter-spacing:2px;
                  color:#9A8578;margin-bottom:14px">
        Login Details
      </div>

      <!-- Time -->
      <div style="display:flex;align-items:flex-start;
                  gap:12px;margin-bottom:12px">
        <span style="font-size:18px">🕐</span>
        <div>
          <div style="font-size:11px;color:#9A8578;
                      text-transform:uppercase;letter-spacing:1px">
            Time
          </div>
          <div style="font-size:14px;font-weight:600;
                      color:#2C1810;margin-top:2px">
            {login_time}
          </div>
        </div>
      </div>

      <!-- Browser -->
      <div style="display:flex;align-items:flex-start;
                  gap:12px;margin-bottom:12px">
        <span style="font-size:18px">🌐</span>
        <div>
          <div style="font-size:11px;color:#9A8578;
                      text-transform:uppercase;letter-spacing:1px">
            Browser
          </div>
          <div style="font-size:14px;font-weight:600;
                      color:#2C1810;margin-top:2px">
            {device['browser']}
          </div>
        </div>
      </div>

      <!-- OS -->
      <div style="display:flex;align-items:flex-start;
                  gap:12px;margin-bottom:12px">
        <span style="font-size:18px">💻</span>
        <div>
          <div style="font-size:11px;color:#9A8578;
                      text-transform:uppercase;letter-spacing:1px">
            Operating System
          </div>
          <div style="font-size:14px;font-weight:600;
                      color:#2C1810;margin-top:2px">
            {device['os']}
          </div>
        </div>
      </div>

      <!-- IP -->
      <div style="display:flex;align-items:flex-start;gap:12px">
        <span style="font-size:18px">📍</span>
        <div>
          <div style="font-size:11px;color:#9A8578;
                      text-transform:uppercase;letter-spacing:1px">
            IP Address
          </div>
          <div style="font-size:14px;font-weight:600;
                      color:#2C1810;margin-top:2px;
                      font-family:monospace">
            {device['ip']}
          </div>
        </div>
      </div>
    </div>

    <!-- Was this you? -->
    <div style="background:#F0FDF4;border-radius:10px;
                border:1px solid #A7F3D0;
                padding:14px 18px;margin-bottom:14px">
      <div style="font-size:13px;font-weight:700;
                  color:#065F46;margin-bottom:4px">
        ✅ Was this you?
      </div>
      <div style="font-size:13px;color:#047857">
        Great! No action needed. You can safely ignore this email.
      </div>
    </div>

    <!-- Was this NOT you? -->
    <div style="background:#FEF2F2;border-radius:10px;
                border:1px solid #FECACA;
                padding:14px 18px">
      <div style="font-size:13px;font-weight:700;
                  color:#991B1B;margin-bottom:4px">
        ⚠️ Wasn't you?
      </div>
      <div style="font-size:13px;color:#B91C1C;
                  margin-bottom:10px">
        Change your password immediately to secure your account.
      </div>
      <a href="https://mbmaniyar.onrender.com/change-password"
         style="display:inline-block;
                background:#7B1C2E;color:#E8B96A;
                text-decoration:none;
                padding:8px 20px;border-radius:50px;
                font-size:12px;font-weight:700;
                letter-spacing:0.5px">
        Change Password Now →
      </a>
    </div>

  </div>

  <!-- Footer -->
  <div style="background:#F5F0EB;padding:16px 32px;
              text-align:center;border-top:1px solid #E8DDD4">
    <p style="font-size:11px;color:#9A8578;margin:0">
      M.B Maniyar Cloth Store · Main Road, Mantha, Jalna
      · <a href="tel:9421474678"
           style="color:#7B1C2E">+91 94214 74678</a>
    </p>
    <p style="font-size:10px;color:#BEB0A6;margin:4px 0 0">
      This is an automated security alert. Do not reply.
    </p>
  </div>

</div>
</body>
</html>
            """
        )

        mail.send(msg)
        print(f"  ✅ Login alert sent to {user.email}")

    except Exception as e:
        # IMPORTANT: Never crash the login if email fails
        # Just log it and continue
        print(f"  ⚠️  Login alert email failed (login still worked): {e}")


def send_password_changed_alert(user, request):
    """
    Sends an alert when the user successfully changes their password.
    This is critical - if someone else changed it, the real user is warned.
    """

    if not user.email or user.email.endswith('@mbmaniyar.local'):
        return

    if not current_app.config.get('MAIL_ENABLED'):
        return

    try:
        from app import mail
        from flask_mail import Message

        device   = get_device_info(request)
        changed_time = datetime.now().strftime('%A, %d %B %Y at %I:%M %p')

        msg = Message(
            subject    = "🔑 Your M.B Maniyar Password Was Changed",
            recipients = [user.email],
            body = f"""
Password Changed - Security Alert

Hi {user.full_name},

Your M.B Maniyar account password was successfully changed.

Details:
  Time      : {changed_time}
  Browser   : {device['browser']}
  System    : {device['os']}
  IP Address: {device['ip']}

If you made this change, you can safely ignore this email.

If you did NOT change your password, contact us IMMEDIATELY:
  Phone: +91 94214 74678

- M.B Maniyar Security Team
            """.strip(),
            html = f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F5F0EB;
             font-family:'Helvetica Neue',Arial,sans-serif">
<div style="max-width:580px;margin:2rem auto;background:#fff;
            border-radius:16px;overflow:hidden;
            box-shadow:0 4px 30px rgba(0,0,0,0.08)">
  <div style="background:linear-gradient(135deg,#560D1E,#7B1C2E);
              padding:28px 32px">
    <div style="font-size:18px;font-weight:900;color:#E8B96A">
      M.B Maniyar
    </div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);
                letter-spacing:2px;text-transform:uppercase;
                margin-top:2px">
      Password Changed
    </div>
  </div>
  <div style="padding:28px 32px">
    <div style="text-align:center;margin-bottom:20px">
      <div style="font-size:48px;margin-bottom:8px">🔑</div>
      <h2 style="font-size:20px;font-weight:700;
                 color:#2C1810;margin:0">
        Password Successfully Changed
      </h2>
      <p style="color:#7A6358;font-size:14px;margin:6px 0 0">
        Hi <strong>{user.full_name}</strong>,
        your account password was just updated.
      </p>
    </div>
    <div style="background:#FDF6EE;border-radius:12px;
                border:1px solid #E8DDD4;padding:20px 24px;
                margin:20px 0">
      <div style="font-size:10px;font-weight:700;
                  text-transform:uppercase;letter-spacing:2px;
                  color:#9A8578;margin-bottom:12px">
        Change Details
      </div>
      <div style="font-size:14px;color:#2C1810;line-height:2">
        🕐 <strong>{changed_time}</strong><br>
        🌐 <strong>{device['browser']}</strong>
            on {device['os']}<br>
        📍 <strong style="font-family:monospace">
           {device['ip']}</strong>
      </div>
    </div>
    <div style="background:#FEF2F2;border-radius:10px;
                border:1px solid #FECACA;padding:14px 18px">
      <div style="font-size:13px;font-weight:700;
                  color:#991B1B;margin-bottom:4px">
        ⚠️ Didn't change your password?
      </div>
      <div style="font-size:13px;color:#B91C1C">
        Call us immediately at
        <strong>+91 94214 74678</strong>
      </div>
    </div>
  </div>
  <div style="background:#F5F0EB;padding:16px 32px;
              text-align:center;border-top:1px solid #E8DDD4">
    <p style="font-size:11px;color:#9A8578;margin:0">
      M.B Maniyar Cloth Store · Main Road, Mantha, Jalna
    </p>
  </div>
</div>
</body></html>
            """
        )
        mail.send(msg)
        print(f"  ✅ Password change alert sent to {user.email}")

    except Exception as e:
        print(f"  ⚠️  Password alert email failed: {e}")
""")

# ══════════════════════════════════════════════════════════════════
# 2. Patch auth/routes.py - add login alert call after login_user()
# ══════════════════════════════════════════════════════════════════
print("\n🔧 Patching auth/routes.py...")

auth_path = os.path.join(BASE, "app/auth/routes.py")
with open(auth_path, 'r') as f:
    content = f.read()

# Patch 1: Add login alert after login_user()
if 'send_login_alert' not in content:
    content = content.replace(
        "login_user(user)\n            nxt = request.args.get('next')",
        """login_user(user)
            # Send security alert email in background
            # (fails silently if email not configured)
            try:
                from app.security_emails import send_login_alert
                send_login_alert(user, request)
            except Exception as e:
                print(f"Login alert error: {e}")
            nxt = request.args.get('next')"""
    )
    print("  ✅ Login alert added to login route")
else:
    print("  ⏭️  Login alert already patched")

# Patch 2: Add password change alert after successful change
if 'send_password_changed_alert' not in content:
    content = content.replace(
        "current_user.password_hash = generate_password_hash(new_pw)\n        db.session.commit()\n        flash('Password changed successfully!",
        """current_user.password_hash = generate_password_hash(new_pw)
        db.session.commit()
        # Alert user that their password was changed
        try:
            from app.security_emails import send_password_changed_alert
            send_password_changed_alert(current_user, request)
        except Exception as e:
            print(f"Password alert error: {e}")
        flash('Password changed successfully!"""
    )
    print("  ✅ Password change alert added")
else:
    print("  ⏭️  Password alert already patched")

with open(auth_path, 'w') as f:
    f.write(content)

# ══════════════════════════════════════════════════════════════════
# 3. Quick test script
# ══════════════════════════════════════════════════════════════════
print("\n📝 Creating test script...")

w("test_login_alert.py", r"""
# test_login_alert.py
# Tests the login security alert without needing a browser
# Run: python3 test_login_alert.py

import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail

app = Flask(__name__)
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER', 'smtp-relay.brevo.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
app.config['MAIL_ENABLED']        = True
app.config['SECRET_KEY']          = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_temp.db'

from flask_mail import Mail
mail = Mail(app)

# Fake user object for testing
class FakeUser:
    full_name = "Krish Maniyar"
    email     = os.environ.get('TEST_EMAIL', 'test@example.com')

# Fake request object
class FakeRequest:
    class headers:
        @staticmethod
        def get(key, default=''):
            fake = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0',
                'X-Forwarded-For': '103.45.67.89',
            }
            return fake.get(key, default)
    remote_addr = '103.45.67.89'

with app.app_context():
    from app.security_emails import send_login_alert, send_password_changed_alert

    print("🔐 Sending test login alert...")
    send_login_alert(FakeUser(), FakeRequest())

    print("🔑 Sending test password change alert...")
    send_password_changed_alert(FakeUser(), FakeRequest())

    print("\n✅ Done! Check your inbox for both security emails.")
""")

print(f"""
╔══════════════════════════════════════════════╗
║  ✅ Step 3 Built!                            ║
╠══════════════════════════════════════════════╣
║  Now run:                                    ║
║  python3 test_login_alert.py                 ║
║                                              ║
║  Then run your app:                          ║
║  python3 run.py                              ║
║                                              ║
║  Login at localhost:5000/login               ║
║  → Security email arrives in inbox ✅        ║
╚══════════════════════════════════════════════╝
""")
