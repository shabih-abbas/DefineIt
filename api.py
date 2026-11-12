from urllib.parse import quote

import requests

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"


class DictionaryError(Exception):
    """Carries a message that is safe to show directly to the user."""


def fetch_word(word):
    try:
        response = requests.get(API_URL + quote(word), timeout=10)
    except requests.exceptions.RequestException as e:
        raise DictionaryError("Oops! We ran into a connection error.") from e

    if response.status_code == 404:
        raise DictionaryError(f"No definitions found for “{word}”.")

    try:
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        raise DictionaryError("The dictionary service sent an unexpected response.") from e


def normalize(data, query):
    if not isinstance(data, list) or not data:
        raise DictionaryError(f"No definitions found for “{query}”.")

    phonetic = ""
    grouped = {}  # partOfSpeech -> [definitions]; dicts keep insertion order

    for item in data:
        phonetic = (
            phonetic
            or item.get("phonetic")
            or next((p["text"] for p in item.get("phonetics", []) if p.get("text")), "")
        )
        for meaning in item.get("meanings", []):
            pos = meaning.get("partOfSpeech") or "other"
            defs = grouped.setdefault(pos, [])
            for d in meaning.get("definitions", []):
                if not d.get("definition"):
                    continue
                entry = {"definition": d["definition"]}
                if d.get("example"):
                    entry["example"] = d["example"]
                defs.append(entry)

    return {
        "word": data[0].get("word", query),
        "phonetic": phonetic,
        "meanings": [{"partOfSpeech": pos, "definitions": defs} for pos, defs in grouped.items()],
    }


def lookup(word):
    return normalize(fetch_word(word), word)