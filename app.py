# app.py
from flask import Flask, Response
import os
from threading import Thread
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

# Configuration
MIRROR_URL = "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"
CHECK_INTERVAL = 10  # seconds between checks

# In-memory store for the current big word
global_big_word = None

@app.route('/')
def home():
    return Response('WOS Big Word API running.', mimetype='text/plain')

@app.route('/bigword')
def get_big_word():
    """Return the current big word in plain text, or fallback message."""
    return Response(global_big_word or 'The big word has not been found yet.', mimetype='text/plain')

# Background scraping loop
def scrape_loop():
    global global_big_word
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)

    last_word = ""
    while True:
        try:
            driver.get(MIRROR_URL)
            time.sleep(3)  # allow JS to render
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            words = [w.text.strip() for w in soup.select('.guessed-words .word')]
            if words:
                longest = max(words, key=len)
                if longest != last_word:
                    global_big_word = longest.upper()
                    print(f"[UPDATE] New big word: {global_big_word}")
                    last_word = longest
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(CHECK_INTERVAL)

# Start scraper thread
t = Thread(target=scrape_loop, daemon=True)
t.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
