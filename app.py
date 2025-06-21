# app.py
from flask import Flask
import socketio
import eventlet
import threading

# === CONFIG ===
MIRROR_ID = "ad66e7bc-81d9-435e-963c-a6159cb13282"
big_word = None

# === FLASK SETUP ===
app = Flask(__name__)

@app.route("/")
def index():
    return "WOS Big Word API running on Render."

@app.route("/bigword")
def get_big_word():
    return big_word or "The big word has not been found yet."

# === SOCKET.IO CLIENT ===
sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("[INFO] Connected to WOS server")
    # Join the mirror channel
    sio.emit('join', {'room': MIRROR_ID})

@sio.on('word')
def on_word(data):
    global big_word
    word = data.get('word', '').strip()
    if word and (len(word) > (len(big_word) if big_word else 0)):
        big_word = word.upper()
        print(f"[UPDATE] New big word: {big_word}")

def start_socket():
    try:
        sio.connect(
            'https://wos.gg',
            transports=['websocket'],
            socketio_path='socket.io',
            query_string={'channel': MIRROR_ID}
        )
        sio.wait()
    except Exception as e:
        print(f"[ERROR] Socket.IO connection failed: {e}")

# === START THREADS AND SERVER ===
th = threading.Thread(target=start_socket, daemon=True)
th.start()

# Serve Flask with Eventlet
if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 10000)), app)
