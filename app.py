# app.py (API-only version)
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# In-memory store for the current big word
global_big_word = None

@app.route('/api/bigword', methods=['GET'])
def get_big_word():
    """Return the current big word or a "not found" message."""
    if global_big_word:
        return jsonify(word=global_big_word)
    return jsonify(word=None, message="The big word has not been found yet."), 200

@app.route('/api/set/<word>', methods=['POST', 'GET'])
def set_big_word(word):
    """Set a new big word via API call."""
    global global_big_word
    global_big_word = word.upper()
    return jsonify(success=True, word=global_big_word), 200

if __name__ == '__main__':
    # Bind to the port provided by Render or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
