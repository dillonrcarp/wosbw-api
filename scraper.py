import os
import re
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
from app import update_big_word, update_all_letters

# Mirror URL override via environment variable
TARGET_URL = os.getenv(
    "WOS_MIRROR_URL",
    "https://wos.gg/r/ad66e7bc-81d9-435e7bc-81d9-435e-963c-a6159cb13282"
)
# How often to poll (in seconds)
SCRAPE_INTERVAL = 2


def setup_driver():
    """Install and configure a headless Chrome WebDriver."""
    chromedriver_autoinstaller.install()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # For Render: point to system Chromium
    options.binary_location = "/usr/bin/chromium"
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    return driver


def extract_big_word_and_letters(soup):
    """Extract the 'big word' container and its letters."""
    hit = soup.find("div", class_=re.compile(r"Slot_hitMax"))
    if not hit:
        return None, []
    spans = hit.find_all("span", class_=re.compile(r"Slot_letter"))
    letters = [span.get_text(strip=True) for span in spans if span.get_text(strip=True).isalpha()]
    word = "".join(letters)
    return word, letters


def scrape_loop():
    """Continuously fetch the mirror page, extract the big word and update state."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting scrape loop...")
    driver = setup_driver()
    try:
        while True:
            try:
                driver.get(TARGET_URL)
                # give JS a moment to render the big word
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Extract big word and letters
                word, letters = extract_big_word_and_letters(soup)
                if letters:
                    update_all_letters(letters)
                    logging.debug(f"Letters: {letters}")
                if word:
                    update_big_word(word)
                    logging.info(f"Big word found: {word}")
                else:
                    logging.debug("No big word container found this iteration.")

            except Exception as e:
                logging.error(f"Error during scrape iteration: {e}")

            time.sleep(SCRAPE_INTERVAL)
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_loop()
