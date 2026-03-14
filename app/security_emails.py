
# app/security_emails.py
# PURPOSE : Send security emails - login alerts and password change alerts

import os
from datetime import datetime


def get_device_info(request):
    """Gets browser, OS and IP from the HTTP request."""
    ua = request.headers.get('User-Agent', 'Unknown')

    if 'Chrome' in ua and 'Edg' not in ua:
        browser = 'Google Chrome'
    elif 'Firefox' in ua:
        browser = 'Mozilla Firefox'
    elif 'Safari' in ua and 'Chrome' not in ua:
        browser = 'Safari'
    elif 'Edg' in ua:
        browser = 'Microsoft Edge'
    else:
        browser = 'Unknown Browser'

    if 'Windows NT 10' in ua:
        os_name = 'Windows 10/11'
    elif 'Android' in ua:
        os_name = 'Android'
    elif 'iPhone' in ua or 'iPad' in ua:
        os_name = 'iOS'
    elif 'Macintosh' in ua:
        os_name = 'macOS'
    elif 'Linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Unknown OS'

    ip = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.headers.get('X-Real-IP', '')
        or request.remote_addr
        or 'Unknown IP'
    )

    return {'browser': browser, 'os': os_name, 'ip': ip}


def send_login_alert(user, request):
    """Sends a login security alert. Fails silently - never crashes the login."""
    if not user.email or '@mbmaniyar.local' in user.email:
        return

    from flask import current_app
    if not current_app.config.get('MAIL_ENABLED'):
        print(f"[MAIL DISABLED] Skipping login alert for {user.email}")
        return

    try:
        from app import mail
        from flask_mail import Message

        device = get_device_info(request)
        login_time = datetime.now().strftime('%A, %d %B %Y at %I:%M %p')

        subject = "New Login to Your M.B Maniyar Account"

        body = (
            "Security Alert - New Login Detected\n\n"
            "Hi " + user.full_name + ",\n\n"
            "A new login was detected on your account.\n\n"
            "Time     : " + login_time + "\n"
            "Browser  : " + device['browser'] + "\n"
            "System   : " + device['os'] + "\n"
            "IP       : " + device['ip'] + "\n\n"
            "If this was you, no action needed.\n"
            "If NOT you, change your password at:\n"
            "https://mbmaniyar.onrender.com/change-password\n\n"
            "- M.B Maniyar Security Team"
        )

        html = (
            "<div style='font-family:Arial,sans-serif;max-width:560px;margin:0 auto'>"
            "<div style='background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0'>"
            "<div style='font-size:20px;font-weight:900;color:#E8B96A'>M.B Maniyar</div>"
            "<div style='font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:2px'>SECURITY ALERT</div>"
            "</div>"
            "<div style='background:#fff;padding:28px;border:1px solid #E8DDD4;border-top:none'>"
            "<div style='text-align:center;margin-bottom:20px'>"
            "<div style='font-size:44px'>🔐</div>"
            "<h2 style='color:#2C1810;margin:8px 0'>New Login Detected</h2>"
            "<p style='color:#7A6358;margin:4px 0'>Hi <strong>" + user.full_name + "</strong>, "
            "someone just signed into your account.</p>"
            "</div>"
            "<div style='background:#FDF6EE;border-radius:10px;border:1px solid #E8DDD4;padding:20px;margin:16px 0'>"
            "<div style='font-size:10px;font-weight:700;text-transform:uppercase;"
            "letter-spacing:2px;color:#9A8578;margin-bottom:14px'>Login Details</div>"
            "<table style='width:100%;font-size:14px'>"
            "<tr><td style='padding:6px 0;color:#9A8578'>Time</td>"
            "<td style='font-weight:600;color:#2C1810'>" + login_time + "</td></tr>"
            "<tr><td style='padding:6px 0;color:#9A8578'>Browser</td>"
            "<td style='font-weight:600;color:#2C1810'>" + device['browser'] + "</td></tr>"
            "<tr><td style='padding:6px 0;color:#9A8578'>System</td>"
            "<td style='font-weight:600;color:#2C1810'>" + device['os'] + "</td></tr>"
            "<tr><td style='padding:6px 0;color:#9A8578'>IP Address</td>"
            "<td style='font-weight:600;color:#2C1810;font-family:monospace'>" + device['ip'] + "</td></tr>"
            "</table>"
            "</div>"
            "<div style='background:#F0FDF4;border-radius:8px;border:1px solid #A7F3D0;"
            "padding:14px;margin-bottom:10px'>"
            "<div style='font-weight:700;color:#065F46;font-size:13px'>This was you?</div>"
            "<div style='color:#047857;font-size:13px;margin-top:4px'>Great! No action needed.</div>"
            "</div>"
            "<div style='background:#FEF2F2;border-radius:8px;border:1px solid #FECACA;padding:14px'>"
            "<div style='font-weight:700;color:#991B1B;font-size:13px'>Was NOT you?</div>"
            "<div style='color:#B91C1C;font-size:13px;margin:4px 0 10px'>"
            "Change your password immediately.</div>"
            "<a href='https://mbmaniyar.onrender.com/change-password' "
            "style='background:#7B1C2E;color:#E8B96A;padding:8px 20px;"
            "border-radius:50px;font-size:12px;font-weight:700;text-decoration:none'>"
            "Change Password Now</a>"
            "</div>"
            "</div>"
            "<div style='background:#F5F0EB;padding:14px;text-align:center;"
            "border-top:1px solid #E8DDD4;font-size:11px;color:#9A8578'>"
            "M.B Maniyar Cloth Store - Main Road, Mantha, Jalna - +91 94214 74678"
            "</div></div>"
        )

        msg = Message(subject=subject, recipients=[user.email], body=body, html=html)
        mail.send(msg)
        print(f"  Login alert sent to {user.email}")

    except Exception as e:
        # Never crash login if email fails
        print(f"  Login alert skipped: {e}")


def send_password_changed_alert(user, request):
    """Sends alert when password is changed."""
    if not user.email or '@mbmaniyar.local' in user.email:
        return

    from flask import current_app
    if not current_app.config.get('MAIL_ENABLED'):
        return

    try:
        from app import mail
        from flask_mail import Message

        device = get_device_info(request)
        changed_time = datetime.now().strftime('%A, %d %B %Y at %I:%M %p')

        subject = "Your M.B Maniyar Password Was Changed"

        body = (
            "Password Changed - Security Alert\n\n"
            "Hi " + user.full_name + ",\n\n"
            "Your password was successfully changed.\n\n"
            "Time   : " + changed_time + "\n"
            "Browser: " + device['browser'] + "\n"
            "System : " + device['os'] + "\n"
            "IP     : " + device['ip'] + "\n\n"
            "If you did NOT change your password,\n"
            "call us immediately: +91 94214 74678\n\n"
            "- M.B Maniyar Security Team"
        )

        html = (
            "<div style='font-family:Arial,sans-serif;max-width:560px;margin:0 auto'>"
            "<div style='background:#7B1C2E;padding:24px;border-radius:12px 12px 0 0'>"
            "<div style='font-size:20px;font-weight:900;color:#E8B96A'>M.B Maniyar</div>"
            "<div style='font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:2px'>PASSWORD CHANGED</div>"
            "</div>"
            "<div style='background:#fff;padding:28px;border:1px solid #E8DDD4;border-top:none'>"
            "<div style='text-align:center;margin-bottom:20px'>"
            "<div style='font-size:44px'>🔑</div>"
            "<h2 style='color:#2C1810;margin:8px 0'>Password Successfully Changed</h2>"
            "<p style='color:#7A6358'>Hi <strong>" + user.full_name + "</strong>, "
            "your account password was just updated.</p>"
            "</div>"
            "<div style='background:#FDF6EE;border-radius:10px;border:1px solid #E8DDD4;padding:20px;margin:16px 0'>"
            "<table style='width:100%;font-size:14px'>"
            "<tr><td style='padding:6px 0;color:#9A8578'>Time</td>"
            "<td style='font-weight:600;color:#2C1810'>" + changed_time + "</td></tr>"
            "<tr><td style='padding:6px 0;color:#9A8578'>Browser</td>"
            "<td style='font-weight:600;color:#2C1810'>" + device['browser'] + "</td></tr>"
            "<tr><td style='padding:6px 0;color:#9A8578'>IP</td>"
            "<td style='font-weight:600;font-family:monospace;color:#2C1810'>" + device['ip'] + "</td></tr>"
            "</table>"
            "</div>"
            "<div style='background:#FEF2F2;border-radius:8px;border:1px solid #FECACA;padding:14px'>"
            "<div style='font-weight:700;color:#991B1B;font-size:13px'>Didn't change your password?</div>"
            "<div style='color:#B91C1C;font-size:13px;margin-top:4px'>"
            "Call us immediately at <strong>+91 94214 74678</strong></div>"
            "</div>"
            "</div>"
            "<div style='background:#F5F0EB;padding:14px;text-align:center;"
            "font-size:11px;color:#9A8578;border-top:1px solid #E8DDD4'>"
            "M.B Maniyar Cloth Store - Mantha, Jalna"
            "</div></div>"
        )

        msg = Message(subject=subject, recipients=[user.email], body=body, html=html)
        mail.send(msg)
        print(f"  Password change alert sent to {user.email}")

    except Exception as e:
        print(f"  Password alert skipped: {e}")
