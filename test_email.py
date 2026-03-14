#!/usr/bin/env python3
# test_email.py — Fixed version for Brevo SMTP
# Run: python3 test_email.py

import os
from dotenv import load_dotenv

# Load .env FIRST before anything else
load_dotenv()

from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# ── Read ALL settings from .env (nothing hardcoded) ───────────────
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER',  'smtp-relay.brevo.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# ── Everything must happen INSIDE app_context ─────────────────────
with app.app_context():

    print("=" * 50)
    print("  MBM Email System — Connection Test")
    print("=" * 50)

    username = os.environ.get('MAIL_USERNAME', 'NOT SET')
    password = os.environ.get('MAIL_PASSWORD', 'NOT SET')
    server   = app.config['MAIL_SERVER']
    recipient = os.environ.get('TEST_EMAIL', username)  # fallback to sender

    print(f"\n🔍 Config check:")
    print(f"   MAIL_SERVER   : {server}")
    print(f"   MAIL_USERNAME : {username}")
    print(f"   MAIL_PASSWORD : {password[:4]}{'*' * 10}")
    print(f"   Sending to    : {recipient}")
    print()

    try:
        msg = Message(
            subject    = "✅ MBM Store — Email Test (Brevo)",
            recipients = [recipient],
            body       = """
Hello from M.B Maniyar Cloth Store!

This test confirms:
  ✅ Brevo SMTP connection works
  ✅ TLS encryption is active
  ✅ Flask-Mail is configured correctly

Store: M.B Maniyar Cloth Store
Location: Main Road, Opp. Bus Stand, Mantha, Jalna
Contact: +91 94214 74678
            """.strip()
        )

        mail.send(msg)
        print("✅ Email sent successfully!")
        print("   Check your inbox — subject: '✅ MBM Store — Email Test (Brevo)'")
        print("   (Also check Spam folder just in case)")
        print()
        print("🎉 Step 1 Complete! Confirm it arrived and we build Step 2 (PDF invoices)")

    except Exception as e:
        print(f"❌ Failed: {e}")
        print()
        print("Fix checklist:")
        print("  1. Is MAIL_SERVER=smtp-relay.brevo.com in your .env?")
        print("  2. Is MAIL_USERNAME your Brevo login email?")
        print("  3. Is MAIL_PASSWORD the SMTP key from Brevo dashboard?")
        print("     (Settings → SMTP & API → SMTP tab → Generate key)")
        print("  4. Did you verify your Brevo account email?")

print("=" * 50)
