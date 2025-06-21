# app.py (Plain text API)
from flask import Flask, Response
import os

app = Flask(__name__)

# In-memory store for the current big word
global_big_word = None

@app.route('/')
def home():
    return Response('WOS Big Word API running.', mimetype='text/plain')

@app.route('/bigword')
def get_big_word():
    """Return the current big word or a not-found message in plain text."""
    if global_big_word:
        return Response(global_big_word, mimetype='text/plain')
    return Response('The big word has not been found yet.', mimetype='text/plain')

@app.route('/set/<word>', methods=['POST', 'GET'])
def set_big_word(word):
    """Set a new big word via API call and return confirmation in plain text."""
    global global_big_word
    global_big_word = word.upper()
    return Response(f'Big word set to: {global_big_word}', mimetype='text/plain')

if __name__ == '__main__':
    # Use PORT env var for Render or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
