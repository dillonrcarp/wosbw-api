from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup
import time
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

app = Flask(__name__)

MIRROR_URL = "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"
CHECK_INTERVAL = 10
big_word = None

@app.route("/")
def index():
    return "WOS Big Word API running on Render."

@app.route("/bigword")
def get_big_word():
    return big_word or "The big word has not been found yet."

def scrape_loop():
    global big_word
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    last_word = ""

    while True:
        try:
            driver.get(MIRROR_URL)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            words = [w.text.strip() for w in soup.select(".guessed-words .word")]
            if words:
                longest = max(words, key=len)
                if longest != last_word:
                    big_word = longest.upper()
                    print(f"Big word updated: {big_word}")
                    last_word = longest
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)

Thread(target=scrape_loop, daemon=True).start()
