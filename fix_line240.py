#!/usr/bin/env python3
import os

path = os.path.expanduser("~/Desktop/mbmaniyar/app/admin/routes.py")

with open(path, 'r') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("Lines 235-250:")
for i, line in enumerate(lines[234:250], start=235):
    print(f"  {i}: {repr(line)}")

# Fix: find the broken 'if' with no body and insert the missing lines
fixed = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.rstrip()
    
    # Detect a bare 'if' statement that ends with ':' but next line is NOT indented more
    if stripped.endswith(':') and 'if User.query.filter_by(username=username)' in stripped:
        fixed.append(line)
        # Check if next line has the flash statement already
        next_line = lines[i+1].strip() if i+1 < len(lines) else ''
        if next_line.startswith('flash(') or next_line.startswith('return '):
            # Already has body, just continue
            i += 1
            continue
        else:
            # Missing body — insert it
            indent = len(line) - len(line.lstrip()) + 4
            sp = ' ' * indent
            fixed.append(f"{sp}flash('Username already taken. Choose a different one.','danger')\n")
            fixed.append(f"{sp}return render_template('admin/employee_form.html',emp=None)\n")
            i += 1
            continue
    fixed.append(line)
    i += 1

with open(path, 'w') as f:
    f.writelines(fixed)

print("\n✅ Done! Verifying lines 235-252 now:")
with open(path, 'r') as f:
    lines2 = f.readlines()
for i, line in enumerate(lines2[234:252], start=235):
    print(f"  {i}: {repr(line)}")

print("\nRun: python3 run.py")
