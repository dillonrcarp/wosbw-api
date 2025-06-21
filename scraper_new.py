import logging
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from app import update_big_word, update_all_letters
import chromedriver_autoinstaller

def setup_chrome_driver():
    """Set up Chrome WebDriver with appropriate options"""
    chromedriver_autoinstaller.install()
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_visible_letters(soup):
    """Extract actual visible scrambled letters from the game interface"""
    all_letters = []
    
    # Strategy 1: Look for elements with single letter content in game areas
    game_areas = soup.find_all(['div'], class_=re.compile(r'anagram|game', re.IGNORECASE))
    
    for area in game_areas:
        # Find all small elements that might contain single letters
        letter_candidates = area.find_all(['div', 'span', 'button', 'p'])
        
        for elem in letter_candidates:
            text = elem.get_text().strip()
            # Look for elements that contain exactly one letter
            if len(text) == 1 and text.isalpha():
                all_letters.append(text.upper())
                logging.debug(f"Found visible letter: {text.upper()}")
    
    # Strategy 2: Look specifically for letter-related CSS classes
    letter_elements = soup.find_all(['div', 'span', 'button'], 
                                  class_=re.compile(r'letter', re.IGNORECASE))
    
    for elem in letter_elements:
        text = elem.get_text().strip()
        if len(text) == 1 and text.isalpha():
            all_letters.append(text.upper())
            logging.debug(f"Found letter element: {text.upper()}")
    
    # Strategy 3: Look for text nodes that are single letters in the game context
    all_text_nodes = soup.find_all(text=re.compile(r'^[A-Za-z]$'))
    for text_node in all_text_nodes:
        parent = text_node.parent
        if parent:
            parent_classes = ' '.join(parent.get('class', []))
            # Only consider letters that are in game-related contexts
            if any(keyword in parent_classes.lower() for keyword in ['game', 'anagram', 'letter', 'scramble']):
                letter = text_node.strip().upper()
                if letter.isalpha():
                    all_letters.append(letter)
                    logging.debug(f"Found text node letter: {letter}")
    
    return all_letters

def extract_words_from_page(driver):
    """Extract words from the Words On Stream game page"""
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    # Debug: Show all CSS classes found
    all_classes = set()
    for element in soup.find_all(class_=True):
        if hasattr(element, 'get') and element.get('class'):
            all_classes.update(element['class'])
    
    logging.debug(f"All classes found: {', '.join(sorted(all_classes))}")
    
    # Extract visible scrambled letters
    all_letters_found = extract_visible_letters(soup)
    
    # Extract completed words from game slots
    words = []
    word_slots = soup.find_all('div', class_=re.compile(r'Slot_slot'))
    
    for slot in word_slots:
        letter_spans = slot.find_all('span', class_=re.compile(r'Slot_letter'))
        if letter_spans:
            letters = []
            for span in letter_spans:
                p_tag = span.find('p')
                if p_tag:
                    text = p_tag.get_text().strip()
                    if text and text != '.':
                        letters.append(text)
            
            if letters:
                word = ''.join(letters).upper()
                if word.isalpha() and len(word) >= 3:
                    words.append(word)
                    logging.debug(f"Found completed word: {word}")
    
    # Update global state
    if all_letters_found:
        sorted_letters = sorted(all_letters_found)
        update_all_letters(sorted_letters)
        logging.debug(f"Updated all letters: {', '.join(sorted_letters)} (total: {len(sorted_letters)})")
    
    return words, all_letters_found

def scrape_loop():
    """Main scraping loop that runs continuously"""
    driver = setup_chrome_driver()
    url = "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"
    
    try:
        while True:
            logging.debug(f"Checking Words On Stream at {url}")
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            words, letters = extract_words_from_page(driver)
            
            if words:
                logging.debug(f"Extracted {len(words)} valid words")
                for word in words:
                    update_big_word(word)
                    logging.info(f"Found new word: {word}")
            else:
                logging.warning("No words found on the page")
            
            if letters:
                logging.info(f"Found {len(letters)} scrambled letters")
            else:
                logging.warning("No letters found on the page")
            
            logging.debug("Waiting 2 seconds before next check...")
            time.sleep(2)
            
    except KeyboardInterrupt:
        logging.info("Scraping stopped by user")
    except Exception as e:
        logging.error(f"Error in scraping loop: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scrape_loop()