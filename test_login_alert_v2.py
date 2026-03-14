#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)
app.config['MAIL_SERVER']         = os.environ.get('MAIL_SERVER', 'smtp-relay.brevo.com')
app.config['MAIL_PORT']           = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']        = True
app.config['MAIL_USE_SSL']        = False
app.config['MAIL_USERNAME']       = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']       = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
mail = Mail(app)
recipient = os.environ.get('TEST_EMAIL', os.environ.get('MAIL_USERNAME'))
login_time = datetime.now().strftime('%A, %d %B %Y at %I:%M %p')
print(f"Sending to: {recipient}")
with app.app_context():
    msg = Message(subject="Security Alert - New Login - M.B Maniyar",
                  recipients=[recipient],
                  body=f"New login detected at {login_time} from Chrome on Linux. IP: 103.45.67.89")
    mail.send(msg)
    print("Login alert sent!")
    msg2 = Message(subject="Password Changed - M.B Maniyar",
                   recipients=[recipient],
                   body=f"Your password was changed at {login_time}. If this was not you, call +91 94214 74678")
    mail.send(msg2)
    print("Password alert sent!")
