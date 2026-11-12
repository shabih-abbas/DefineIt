
import json
import os
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent        
SAVED_FILE = BASE_DIR / "saved_words.jsonl"
CONFIG_FILE = BASE_DIR / "config.json"

CHUNK = 4096  


def _path(path):
    return Path(path) if path else SAVED_FILE



def load_config():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(config):
    tmp = CONFIG_FILE.with_suffix(".tmp")           
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    os.replace(tmp, CONFIG_FILE)


def ensure_files():
    
    SAVED_FILE.touch(exist_ok=True)
    if not CONFIG_FILE.exists():
        save_config({})



def _iter_entries(path=None):
    path = _path(path)
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue                          


def is_saved(word, path=None):
    word = word.lower()
    return any(str(e.get("word", "")).lower() == word for e in _iter_entries(path))


def save_word(entry, path=None):
    
    path = _path(path)
    if is_saved(entry["word"], path):
        return False
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return True


def _line_start(f, pos):
    
    end = pos
    while end > 0:
        begin = max(0, end - CHUNK)
        f.seek(begin)
        chunk = f.read(end - begin)
        i = chunk.rfind(b"\n")
        if i != -1:
            return begin + i + 1
        end = begin
    return 0


def _random_entry(path):
    size = path.stat().st_size
    if size == 0:
        return None
    with open(path, "rb") as f:
        pos = random.randrange(size)              
        f.seek(_line_start(f, pos))               
        line = f.readline().decode("utf-8", errors="replace").strip()
    try:
        return json.loads(line) if line else None
    except json.JSONDecodeError:
        return None


def get_random_word(exclude=None, path=None, retries=8):
   
    path = _path(path)
    if not path.exists():
        return None

    skip = (exclude or "").lower()

  
    for _ in range(retries):
        entry = _random_entry(path)
        if entry and str(entry.get("word", "")).lower() != skip:
            return entry

    
    entries = list(_iter_entries(path))
    if not entries:
        return None
    others = [e for e in entries if str(e.get("word", "")).lower() != skip]
    return random.choice(others or entries)