import os
import logging
from flask import Flask, Response, jsonify

# ——— App & Logging —————————————————————————————
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# ——— Health Check ————————————————————————————
@app.route("/healthz")
def healthz():
    return "OK", 200

# ——— Global State & Updaters ————————————————————
big_word = None
big_word_length = 0
all_letters = []

def update_big_word(new_word):
    """
    Called by your scraper thread whenever it finds a candidate.
    Only updates if the new word is strictly longer.
    """
    global big_word, big_word_length
    if new_word and len(new_word) > big_word_length:
        big_word = new_word.upper()
        big_word_length = len(new_word)
        logging.info(f"Big word updated: {big_word} (length: {big_word_length})")
        return True
    return False

def update_all_letters(letters_list):
    """
    Called by your scraper to keep the full pool of letters.
    """
    global all_letters
    all_letters = letters_list
    logging.debug(f"All letters updated ({len(letters_list)}): {', '.join(letters_list)}")

# ——— API Endpoints ————————————————————————————
@app.route("/bigword")
def get_big_word_text():
    """Plain-text endpoint for StreamElements/Nightbot."""
    if big_word:
        return Response(big_word, mimetype="text/plain")
    return Response("No big word found", status=404, mimetype="text/plain")

@app.route("/api/bigword")
def get_big_word_json():
    """Machine-readable JSON endpoint."""
    return jsonify({
        "word": big_word,
        "length": big_word_length,
        "all_letters": all_letters,
        "status": "found" if big_word else "not_found"
    })

# ——— Run Locally ——————————————————————————————
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
