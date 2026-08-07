"""
التخزين المستمر - Persistent Storage
يحفظ Logs في ملف JSON لتبقى بعد إعادة تشغيل Railway
Integrated v4.0
"""
import json
import os
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_FILE = DATA_DIR / "logs.json"

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_logs(logs: List[Dict]):
    try:
        ensure_data_dir()
        # نحفظ آخر 500 فقط لتوفير المساحة
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(logs[:500], f, ensure_ascii=False, indent=1)
    except Exception as e:
        print(f"[STORAGE] save failed: {e}")

def load_logs() -> List[Dict]:
    try:
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[STORAGE] load failed: {e}")
    return []

def append_log(entry: Dict):
    """إضافة سجل واحد للملف بشكل آمن"""
    try:
        logs = load_logs()
        logs.insert(0, entry)
        save_logs(logs[:500])
    except:
        pass
