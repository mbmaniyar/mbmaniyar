#!/usr/bin/env python3
import os

path = os.path.expanduser("~/Desktop/mbmaniyar/app/models.py")

with open(path, 'r') as f:
    content = f.read()

# Fix the ClockRecord date default — replace with lambda so it works regardless of imports
content = content.replace(
    "date        = db.Column(db.Date, default=date.today)",
    "date        = db.Column(db.Date, default=lambda: __import__('datetime').date.today())"
)

# Also ensure datetime is imported at the top
if "from datetime import datetime" in content and "from datetime import datetime, date" not in content:
    content = content.replace(
        "from datetime import datetime",
        "from datetime import datetime, date"
    )
elif "from datetime import" not in content:
    content = "from datetime import datetime, date\n" + content

with open(path, 'w') as f:
    f.write(content)

print("✅ Fixed! Now run:")
print("   python3 seed_step5.py")
print("   python3 run.py")
