from flask import Flask, Response
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# replace with your actual mirror URL
TARGET_URL = "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"

@app.route("/bigword")
def big_word():
    res = requests.get(TARGET_URL, timeout=5)
    if res.status_code != 200:
        return Response("Error fetching source", status=502, mimetype="text/plain")

    soup = BeautifulSoup(res.text, "html.parser")

    # find the slot div whose class contains "Slot_hitMax"
    hit = soup.find(
        "div",
        class_=lambda c: c and "Slot_hitMax" in c
    )
    if not hit:
        return Response("No big word found", status=404, mimetype="text/plain")

    # collect each letter in order
    letters = hit.select("span.Slot_letter__WYkoZ")
    word = "".join(letter.get_text(strip=True) for letter in letters)

    # return as plain text
    return Response(word, mimetype="text/plain")

if __name__ == "__main__":
    # for local testing
    app.run(host="0.0.0.0", port=5000)
