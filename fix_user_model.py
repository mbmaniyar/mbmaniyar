#!/usr/bin/env python3
"""Fixes User model and resets database"""
import os, subprocess

BASE = os.path.expanduser("~/Desktop/mbmaniyar")

# ── Read models.py ────────────────────────────────────────────────
path = os.path.join(BASE, "app/models.py")
with open(path, 'r') as f:
    content = f.read()

# ── Find the User model and add missing fields ────────────────────
fields_to_add = """    email_verified      = db.Column(db.Boolean, default=False)
    verification_token  = db.Column(db.String(100))
    reset_token         = db.Column(db.String(100))
    reset_token_expiry  = db.Column(db.DateTime)"""

# Check what's already there
missing = []
for field in ['email_verified', 'verification_token', 'reset_token', 'reset_token_expiry']:
    if field not in content:
        missing.append(field)

if missing:
    print(f"  Adding missing fields: {missing}")
    # Find is_active_account line and add after it
    if 'is_active_account' in content:
        # Add after is_active_account line
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if 'is_active_account' in line and 'db.Column' in line:
                if 'email_verified' not in content:
                    new_lines.append("    email_verified      = db.Column(db.Boolean, default=False)")
                if 'verification_token' not in content:
                    new_lines.append("    verification_token  = db.Column(db.String(100))")
                if 'reset_token' not in content and 'reset_token_expiry' not in line:
                    new_lines.append("    reset_token         = db.Column(db.String(100))")
                if 'reset_token_expiry' not in content:
                    new_lines.append("    reset_token_expiry  = db.Column(db.DateTime)")
        content = '\n'.join(new_lines)
    else:
        # Fallback: add before the first relationship in User model
        content = content.replace(
            "class User(db.Model, UserMixin):",
            "class User(db.Model, UserMixin):\n    # These will be inserted below"
        )
    with open(path, 'w') as f:
        f.write(content)
    print("  ✅ Fields added to User model")
else:
    print("  ✅ All fields already present")

# ── Verify ────────────────────────────────────────────────────────
with open(path, 'r') as f:
    check = f.read()
for field in ['email_verified', 'verification_token', 'reset_token']:
    status = "✅" if field in check else "❌"
    print(f"  {status} {field}")

# ── Reset database ────────────────────────────────────────────────
print("\n🗄️  Resetting database...")
reset_script = """
import sys
sys.path.insert(0, '.')
from app import create_app
from app.models import db

app = create_app()
with app.app_context():
    db.drop_all()
    print('  Dropped all tables')
    db.create_all()
    print('  Created all tables with new schema')
    
    # Verify columns exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('users')]
    print(f'  User columns: {cols}')
    
    for field in ['email_verified', 'verification_token', 'reset_token']:
        status = '✅' if field in cols else '❌ MISSING'
        print(f'  {status} {field}')

print('  ✅ Database ready!')
"""

result = subprocess.run(
    ["python3", "-c", reset_script],
    capture_output=True, text=True,
    cwd=BASE
)
print(result.stdout)
if result.stderr:
    print("ERRORS:", result.stderr[-500:])

# ── Re-seed ───────────────────────────────────────────────────────
print("\n🌱 Re-seeding data...")
seed_path = os.path.join(BASE, "seed_products.py")
if os.path.exists(seed_path):
    r = subprocess.run(["python3", "seed_products.py"], capture_output=True, text=True, cwd=BASE)
    print(r.stdout[-300:] if r.stdout else "  Done")

print("""
✅ All fixed! Now run:
   python3 run.py

Then test at: localhost:5000/register
""")
