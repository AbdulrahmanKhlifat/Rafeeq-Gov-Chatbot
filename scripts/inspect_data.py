# scripts/inspect_data.py
import os
import json
import re

DATA_DIR = "data"

HEADERS = [
    "الفئة المستفيدة",
    "أماكن تقديم الخدمة",
    "شروط تقديم الخدمة",
    "الوثائق المطلوبة",
    "إجراءات تقديم الخدمة",
    "الزمن المستغرق",
    "شركاء الخدمة",
    "ملاحظات",
    "الرسوم"
]

all_services = {}

for fname in sorted(os.listdir(DATA_DIR)):
    if not fname.endswith(".txt"):
        continue
    service_id = fname[:-4]
    filepath = os.path.join(DATA_DIR, fname)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse fields
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    fields = {}
    current_key = "title"
    buffer = []

    for line in lines:
        matched_h = None
        for h in HEADERS:
            if line.startswith(h):
                matched_h = h
                break
        
        if matched_h:
            if buffer:
                fields[current_key] = "\n".join(buffer).strip()
            current_key = matched_h
            remainder = line[len(matched_h):].strip()
            buffer = [remainder] if remainder else []
        else:
            buffer.append(line)

    if buffer:
        fields[current_key] = "\n".join(buffer).strip()

    all_services[service_id] = fields

with open("src/structured_services.json", "w", encoding="utf-8") as f:
    json.dump(all_services, f, ensure_ascii=False, indent=2)

print(f"Parsed {len(all_services)} services into src/structured_services.json")
