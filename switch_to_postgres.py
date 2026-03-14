#!/usr/bin/env python3
"""
🐘 Switch MBM from SQLite → PostgreSQL
Run AFTER setting up free PostgreSQL on Render
"""
import os, subprocess

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(content)
    print(f"  ✅ {path}")

print("\n🐘 Switching to PostgreSQL\n" + "="*45)

# 1. Install psycopg2
print("\n📦 Installing psycopg2...")
try:
    subprocess.run(["pip", "install", "psycopg2-binary", "--break-system-packages", "-q"], check=True)
    print("  ✅ psycopg2-binary installed")
except:
    subprocess.run(["pip", "install", "psycopg2-binary", "-q"])
    print("  ✅ psycopg2-binary installed")

# 2. Update config.py to handle both SQLite (local) and PostgreSQL (production)
print("\n⚙️  Updating config.py...")
w("app/config.py", """import os
from dotenv import load_dotenv
load_dotenv()

def get_db_url():
    url = os.environ.get('DATABASE_URL', 'sqlite:///mbmaniyar.db')
    # Render gives postgres:// but SQLAlchemy needs postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'mbm-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = get_db_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORE_NAME    = os.environ.get('STORE_NAME', 'M.B Maniyar Cloth Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', 'Main Road, Opposite Bus Stand, Mantha, Jalna')
    STORE_PHONE   = os.environ.get('STORE_PHONE', '+91 94214 74678')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'M.B Maniyar <noreply@mbmaniyar.com>')
    MAIL_ENABLED  = bool(os.environ.get('MAIL_USERNAME', ''))
""")

# 3. Update requirements.txt
print("\n📦 Updating requirements.txt...")
req_path = os.path.join(BASE, "requirements.txt")
with open(req_path, 'r') as f:
    reqs = f.read()
if 'psycopg2' not in reqs:
    with open(req_path, 'a') as f:
        f.write('\npsycopg2-binary>=2.9.9\n')
    print("  ✅ psycopg2-binary added")

# 4. Commit and push
print("\n📤 Pushing to GitHub...")
os.chdir(BASE)
subprocess.run(["git", "add", "."])
result = subprocess.run(
    ["git", "commit", "-m", "Switch to PostgreSQL for persistent storage"],
    capture_output=True, text=True
)
print(" ", result.stdout.strip() or "Nothing new to commit")
subprocess.run(["git", "push", "origin", "main"])

print("""
╔══════════════════════════════════════════════╗
║  ✅ Code ready for PostgreSQL!               ║
╚══════════════════════════════════════════════╝

NOW DO THIS ON RENDER (takes 3 minutes):

STEP 1 — Create free PostgreSQL on Render
  1. render.com → Dashboard
  2. Click "New +" → "PostgreSQL"
  3. Name: mbmaniyar-db
  4. Plan: FREE
  5. Click "Create Database"
  6. Wait ~1 min for it to be ready

STEP 2 — Connect it to your web service
  1. Click your PostgreSQL database
  2. Copy the "Internal Database URL"
     (looks like: postgresql://user:pass@host/dbname)
  3. Go to your mbmaniyar Web Service
  4. Click "Environment" tab
  5. Find DATABASE_URL → paste the Internal URL
  6. Click "Save Changes"

STEP 3 — Redeploy
  Render will auto-redeploy. Your app will now
  use PostgreSQL — data persists FOREVER! 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FREE TIER COMPARISON:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Render Free:  ✅ Flask ✅ PostgreSQL 90 days
  Vercel:       ❌ Bad for Flask
  Railway:      ✅ $5 credit/mo (best paid option)
  Fly.io:       ✅ Flask + persistent volumes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
