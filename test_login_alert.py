#!/usr/bin/env python3
# test_login_alert.py
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

mail = Mail(app)

class FakeUser:
    full_name = "Krish Maniyar"
    email     = os.environ.get('TEST_EMAIL', 'test@example.com')

class FakeRequest:
    class headers:
        @staticmethod
        def get(key, default=''):
            data = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0.0.0',
                'X-Forwarded-For': '103.45.67.89',
                'X-Real-IP': '103.45.67.89',
            }
            return data.get(key, default)
    remote_addr = '103.45.67.89'

print("=" * 45)
print("  Login Alert Email Test")
print("=" * 45)

with app.app_context():
    import sys
    sys.path.insert(0, os.path.expanduser("~/Desktop/mbmaniyar"))
    from app.security_emails import send_login_alert, send_password_changed_alert

    print("\n Sending login alert...")
    send_login_alert(FakeUser(), FakeRequest())

    print(" Sending password change alert...")
    send_password_changed_alert(FakeUser(), FakeRequest())

print("\nDone! Check your inbox for both security emails.")
print("=" * 45)
