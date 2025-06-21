import os
import re
from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

# 1) Create the app first
app = Flask(__name__)

# 2) Health check for Render
@app.route("/healthz")
def healthz():
    return "OK", 200

# 3) Mirror URL (override via env var if you like)
TARGET_URL = os.getenv(
    "WOS_MIRROR_URL",
    "https://wos.gg/r/ad66e7bc-81d9-435e7bc-81d9-435e-963c-a6159cb13282"
)

@app.route("/bigword")
def big_word():
    # Try HTML scrape
    try:
        res = requests.get(TARGET_URL, timeout=5)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        hit = soup.find("div", class_=re.compile(r"Slot_hitMax"))
        if hit:
            letters = hit.find_all("span", class_=re.compile(r"Slot_letter"))
            word = "".join(letter.get_text(strip=True) for letter in letters)
            if word:
                return Response(word, mimetype="text/plain")
    except Exception:
        pass

    # Fallback to JSON endpoint
    try:
        j = requests.get(TARGET_URL + ".json", timeout=5).json()
        word = j.get("big") or j.get("word")
        if word:
            return Response(word, mimetype="text/plain")
    except Exception:
        pass

    # Nothing found
    return Response("No big word found", status=404, mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
