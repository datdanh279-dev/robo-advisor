import re, os
os.environ["PYTHONIOENCODING"] = "utf-8"

with open(r'C:\Users\ACER\robo-advisor\app.py', encoding='utf-8') as f:
    content = f.read()

has_real_checks = []
for i, line in enumerate(content.split('\n'), 1):
    stripped = line.strip()
    if 'has_real' in stripped and ('if' in stripped or 'elif' in stripped):
        has_real_checks.append((i, stripped[:150]))

out = []
out.append("=== has_real checks ===")
for ln, code in has_real_checks:
    out.append(f"  {ln}: {code}")

has_fund_checks = []
for i, line in enumerate(content.split('\n'), 1):
    stripped = line.strip()
    if 'has_fund' in stripped and ('if' in stripped or 'elif' in stripped):
        has_fund_checks.append((i, stripped[:150]))

out.append("\n=== has_fund checks ===")
for ln, code in has_fund_checks:
    out.append(f"  {ln}: {code}")

with open('analysis_out.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f"Written {len(out)} lines to analysis_out.txt")
