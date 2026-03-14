#!/usr/bin/env python3
# patch_auth_alerts.py
# Copies security_emails.py and patches auth/routes.py
import os, shutil

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

# 1. Copy security_emails.py into app/
src = os.path.join(os.path.dirname(__file__), "security_emails.py")
dst = os.path.join(BASE, "app/security_emails.py")

# The file is in the same folder as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(script_dir, "security_emails.py")

shutil.copy(src, dst)
print(f"Copied security_emails.py to app/")

# 2. Patch auth/routes.py
auth_path = os.path.join(BASE, "app/auth/routes.py")
with open(auth_path, 'r') as f:
    content = f.read()

# Patch 1: login alert after login_user()
if 'send_login_alert' not in content:
    content = content.replace(
        "login_user(user)\n            nxt = request.args.get('next')",
        "login_user(user)\n"
        "            try:\n"
        "                from app.security_emails import send_login_alert\n"
        "                send_login_alert(user, request)\n"
        "            except Exception as e:\n"
        "                print(f'Login alert error: {e}')\n"
        "            nxt = request.args.get('next')"
    )
    print("Login alert added to auth routes")
else:
    print("Login alert already in auth routes")

# Patch 2: password change alert
if 'send_password_changed_alert' not in content:
    old = "current_user.password_hash = generate_password_hash(new_pw)\n        db.session.commit()\n        flash('Password changed successfully!"
    new = (
        "current_user.password_hash = generate_password_hash(new_pw)\n"
        "        db.session.commit()\n"
        "        try:\n"
        "            from app.security_emails import send_password_changed_alert\n"
        "            send_password_changed_alert(current_user, request)\n"
        "        except Exception as e:\n"
        "            print(f'Password alert error: {e}')\n"
        "        flash('Password changed successfully!"
    )
    if old in content:
        content = content.replace(old, new)
        print("Password change alert added")
    else:
        print("Could not find password change location - adding manually")
else:
    print("Password alert already in auth routes")

with open(auth_path, 'w') as f:
    f.write(content)

print("\nAll done! Now test with:")
print("  python3 test_login_alert.py")
