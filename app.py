import os
import re
from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Mirror URL (can override via env var)
TARGET_URL = os.getenv(
    "WOS_MIRROR_URL",
    "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"
)

@app.route("/bigword")
def big_word():
    # 1) Try fetching the HTML
    try:
        res = requests.get(TARGET_URL, timeout=5)
        res.raise_for_status()
    except Exception as e:
        return Response(f"Error fetching source: {e}", status=502, mimetype="text/plain")

    soup = BeautifulSoup(res.text, "html.parser")

    # 2) Look for the div whose class contains "Slot_hitMax"
    hit = soup.find("div", class_=re.compile(r"Slot_hitMax"))
    if hit:
        letters = hit.find_all("span", class_=re.compile(r"Slot_letter"))
        word = "".join(letter.get_text(strip=True) for letter in letters)
        if word:
            return Response(word, mimetype="text/plain")

    # 3) Fallback: try the JSON endpoint
    try:
        json_resp = requests.get(TARGET_URL + ".json", timeout=5)
        data = json_resp.json()
        word = data.get("big") or data.get("word")
        if word:
            return Response(word, mimetype="text/plain")
    except Exception:
        pass

    # 4) Nothing found
    return Response("No big word found", status=404, mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
