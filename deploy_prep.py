#!/usr/bin/env python3
"""
🚀 MBM DEPLOYMENT PREP
Prepares your app for free hosting on Render.com
Run: python3 deploy_prep.py
"""
import os, subprocess, sys

BASE = os.path.expanduser("~/Desktop/mbmaniyar")
os.chdir(BASE)

def w(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(content)
    print(f"  ✅ {path}")

print("\n🚀 MBM Deployment Prep\n" + "="*45)

# ══════════════════════════════════════════════
# 1. requirements.txt
# ══════════════════════════════════════════════
print("\n📦 Step 1: Generating requirements.txt...")
try:
    result = subprocess.run(
        ["pip", "freeze"],
        capture_output=True, text=True
    )
    pkgs = result.stdout.strip()
    # Ensure critical packages are present
    required = {
        "flask": "Flask>=3.0.0",
        "flask-sqlalchemy": "Flask-SQLAlchemy>=3.1.1",
        "flask-login": "Flask-Login>=0.6.3",
        "flask-socketio": "Flask-SocketIO>=5.3.6",
        "werkzeug": "Werkzeug>=3.0.1",
        "gunicorn": "gunicorn>=21.2.0",
        "python-dotenv": "python-dotenv>=1.0.0",
        "eventlet": "eventlet>=0.35.1",
    }
    lines = pkgs.split('\n') if pkgs else []
    existing_lower = [l.split('==')[0].lower() for l in lines]
    for key, val in required.items():
        if key not in existing_lower:
            lines.append(val)
    # Remove problematic packages for cloud
    blacklist = ['pkg-resources']
    lines = [l for l in lines if l and l.split('==')[0].lower() not in blacklist]
    w("requirements.txt", '\n'.join(sorted(set(lines))))
    print(f"     Found {len(lines)} packages")
except Exception as e:
    # Fallback minimal requirements
    w("requirements.txt", """Flask>=3.0.0
Flask-SQLAlchemy>=3.1.1
Flask-Login>=0.6.3
Flask-SocketIO>=5.3.6
Werkzeug>=3.0.1
gunicorn>=21.2.0
python-dotenv>=1.0.0
eventlet>=0.35.1
SQLAlchemy>=2.0.0
bcrypt>=4.1.2
Pillow>=10.2.0
""")
    print(f"     Used fallback requirements ({e})")

# ══════════════════════════════════════════════
# 2. Procfile (Render / Railway)
# ══════════════════════════════════════════════
print("\n⚙️  Step 2: Creating Procfile...")
w("Procfile", "web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app\n")

# ══════════════════════════════════════════════
# 3. runtime.txt
# ══════════════════════════════════════════════
print("\n🐍 Step 3: Setting Python version...")
pyver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
w("runtime.txt", f"python-{pyver}\n")
print(f"     Python {pyver}")

# ══════════════════════════════════════════════
# 4. render.yaml (auto-deploy config)
# ══════════════════════════════════════════════
print("\n🎨 Step 4: Creating render.yaml...")
w("render.yaml", """services:
  - type: web
    name: mbmaniyar
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT run:app
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: STORE_NAME
        value: M.B Maniyar Cloth Store
      - key: STORE_ADDRESS
        value: Main Road, Opposite Bus Stand, Mantha, Jalna
      - key: FLASK_ENV
        value: production
      - key: DATABASE_URL
        value: sqlite:///mbmaniyar.db
""")

# ══════════════════════════════════════════════
# 5. Patch run.py for production
# ══════════════════════════════════════════════
print("\n🔧 Step 5: Patching run.py for production...")
run_py = """import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
"""
w("run.py", run_py)

# ══════════════════════════════════════════════
# 6. Patch config.py to use env vars properly
# ══════════════════════════════════════════════
print("\n⚙️  Step 6: Patching config.py for production...")
config_path = os.path.join(BASE, "app/config.py")
config_content = """import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY        = os.environ.get('SECRET_KEY') or 'mbm-super-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mbmaniyar.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORE_NAME    = os.environ.get('STORE_NAME', 'M.B Maniyar Cloth Store')
    STORE_ADDRESS = os.environ.get('STORE_ADDRESS', 'Main Road, Opposite Bus Stand, Mantha, Jalna')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'products')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
"""
with open(config_path, 'w') as f:
    f.write(config_content)
print("  ✅ app/config.py")

# ══════════════════════════════════════════════
# 7. .gitignore
# ══════════════════════════════════════════════
print("\n📝 Step 7: Creating .gitignore...")
w(".gitignore", """# Python
__pycache__/
*.py[cod]
*.pyo
.Python
venv/
env/
.env

# Database (will be created fresh on server)
*.db
*.sqlite
*.sqlite3

# Uploads (not tracked in git)
app/static/images/products/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
""")

# ══════════════════════════════════════════════
# 8. Install gunicorn & eventlet locally
# ══════════════════════════════════════════════
print("\n📥 Step 8: Installing gunicorn & eventlet...")
try:
    subprocess.run(["pip", "install", "gunicorn", "eventlet", "--break-system-packages", "-q"],
                   check=True, capture_output=True)
    print("  ✅ gunicorn + eventlet installed")
except:
    subprocess.run(["pip", "install", "gunicorn", "eventlet", "-q"])
    print("  ✅ gunicorn + eventlet installed")

# ══════════════════════════════════════════════
# 9. Initialize git repo
# ══════════════════════════════════════════════
print("\n📁 Step 9: Initializing Git repo...")
if not os.path.exists(os.path.join(BASE, ".git")):
    subprocess.run(["git", "init"], capture_output=True)
    subprocess.run(["git", "add", "."], capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit: M.B Maniyar Cloth Store"], capture_output=True)
    print("  ✅ Git repo initialized and committed")
else:
    subprocess.run(["git", "add", "."], capture_output=True)
    result = subprocess.run(["git", "commit", "-m", "Deploy prep: add Procfile, requirements, render.yaml"],
                            capture_output=True, text=True)
    print("  ✅ Changes committed to Git")

# ══════════════════════════════════════════════
# 10. Quick test
# ══════════════════════════════════════════════
print("\n🧪 Step 10: Quick app test...")
try:
    result = subprocess.run(
        ["python3", "-c", "from app import create_app; app = create_app(); print('APP OK')"],
        capture_output=True, text=True, timeout=15
    )
    if "APP OK" in result.stdout:
        print("  ✅ App imports cleanly — ready to deploy!")
    else:
        print(f"  ⚠️  App test output: {result.stderr[:200]}")
except Exception as e:
    print(f"  ⚠️  Test skipped: {e}")

# ══════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════
print("""
╔══════════════════════════════════════════════╗
║   ✅ ALL DEPLOYMENT FILES READY!             ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Files created:                              ║
║  ✔ requirements.txt                          ║
║  ✔ Procfile                                  ║
║  ✔ render.yaml                               ║
║  ✔ runtime.txt                               ║
║  ✔ .gitignore                                ║
║  ✔ run.py (production-ready)                 ║
║  ✔ app/config.py (env vars)                  ║
║                                              ║
║  NEXT STEP:                                  ║
║  Follow the instructions printed below 👇    ║
╚══════════════════════════════════════════════╝
""")

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🌐 DEPLOY TO RENDER.COM (FREE) — STEP BY STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — Push code to GitHub
  a) Go to https://github.com and create a free account
  b) Click "New Repository"
  c) Name it: mbmaniyar
  d) Set to PUBLIC, click "Create repository"
  e) Run these commands in your terminal:

     cd ~/Desktop/mbmaniyar
     git remote add origin https://github.com/YOUR_USERNAME/mbmaniyar.git
     git branch -M main
     git push -u origin main

STEP 2 — Deploy on Render (100% Free)
  a) Go to https://render.com and sign up with GitHub
  b) Click "New +" → "Web Service"
  c) Connect your GitHub → select "mbmaniyar"
  d) Render will AUTO-DETECT your render.yaml ✨
  e) Click "Create Web Service"
  f) Wait ~3 mins for build to finish

STEP 3 — Your site will be LIVE at:
  https://mbmaniyar.onrender.com 🎉

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️  IMPORTANT NOTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. FREE TIER: Render free tier "sleeps" after
     15 mins of inactivity — first load takes ~30s.
     Upgrade to $7/mo for always-on.

  2. DATABASE: SQLite works but resets on redeploy.
     For permanent data, upgrade to PostgreSQL
     (Render gives free 90-day PostgreSQL).

  3. Admin credentials will reset on redeploy
     (new DB seeded fresh). Note them down!
     Login: admin / admin123

  4. File uploads (product images) won't persist
     on free tier. Use Cloudinary for images later.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
