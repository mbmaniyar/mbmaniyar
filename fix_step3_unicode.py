#!/usr/bin/env python3
# fix_step3_unicode.py — removes the bad character and reruns the build
import os, re

path = os.path.expanduser("~/Desktop/mbmaniyar/build_step3_login_alerts.py")

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all fancy unicode dashes with a plain hyphen
content = content.replace('\u2014', '-')  # em dash
content = content.replace('\u2013', '-')  # en dash
content = content.replace('\u2019', "'")  # curly apostrophe
content = content.replace('\u2018', "'")  # curly quote

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed! Now running the build...")

import subprocess
result = subprocess.run(
    ["python3", "build_step3_login_alerts.py"],
    cwd=os.path.expanduser("~/Desktop/mbmaniyar")
)
