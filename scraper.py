import time
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import chromedriver_autoinstaller
from app import update_big_word, update_all_letters

# Configuration
MIRROR_URL = "https://wos.gg/r/ad66e7bc-81d9-435e-963c-a6159cb13282"
CHECK_INTERVAL = 2  # Reduced from 10 to 2 seconds for faster updates
TIMEOUT = 10

def setup_chrome_driver():
    """Set up Chrome WebDriver with appropriate options"""
    try:
        import subprocess
        from selenium.webdriver.chrome.service import Service
        
        # Get chromedriver path
        chromedriver_path = subprocess.check_output(['which', 'chromedriver'], text=True).strip()
        service = Service(chromedriver_path)
        
        # Configure Chrome options
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        # Remove the disable-javascript flag to allow dynamic content to load
        # options.add_argument("--disable-javascript")
        
        # Set Chromium binary location
        try:
            chromium_path = subprocess.check_output(['which', 'chromium'], text=True).strip()
            options.binary_location = chromium_path
            logging.info(f"Using Chromium at: {chromium_path}")
        except subprocess.CalledProcessError:
            logging.warning("Chromium not found in PATH")
        
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(TIMEOUT)
        
        logging.info("Chrome WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        logging.error(f"Failed to initialize Chrome WebDriver: {e}")
        return None

def extract_words_from_page(driver):
    """Extract words from the Words On Stream game page"""
    try:
        # Wait for the page to load and get the page source
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Look specifically for game word slots/letters based on the HTML structure
        # From the logs, I can see the structure uses classes like "Slot_letter__WYkoZ"
        
        # Look for ALL letters in the game, including scrambled ones
        import re
        
        # Debug: Log all unique class names to understand the HTML structure
        all_elements_with_classes = soup.find_all(class_=True)
        unique_classes = set()
        for elem in all_elements_with_classes:
            classes = elem.get('class', [])
            for cls in classes:
                unique_classes.add(cls)
        
        logging.debug(f"All classes found: {', '.join(sorted(unique_classes))}")
        
        # Look specifically for classes that might contain scrambled letters
        relevant_classes = [cls for cls in unique_classes if any(keyword in cls.lower() 
                           for keyword in ['letter', 'char', 'tile', 'game', 'slot', 'board', 'pool', 'deck', 'hand'])]
        if relevant_classes:
            logging.debug(f"Relevant letter/game classes: {', '.join(sorted(relevant_classes))}")
        
        # Find all letter elements on the page (both guessed and unguessed)
        all_letter_spans = soup.find_all('span', class_=re.compile(r'Slot_letter'))
        all_letters_found = []
        words = []
        
        # Collect ALL letters from the page - including empty slots and completed words
        for span in all_letter_spans:
            p_tag = span.find('p')
            if p_tag:
                text = p_tag.get_text().strip()
                if text and text != '.' and text.isalpha():
                    all_letters_found.append(text.upper())
                    
        # Look specifically for the anagram/scrambled letter pool
        # Based on debug output, we found "Anagram_letters__C3Frt" class
        anagram_containers = soup.find_all(['div', 'span'], class_=re.compile(r'Anagram_letters'))
        logging.debug(f"Found {len(anagram_containers)} anagram letter containers")
        
        # Track processed container texts to avoid duplicates and get the cleanest one
        container_texts = []
        for container in anagram_containers:
            container_text = container.get_text().strip()
            if container_text:
                container_texts.append(container_text)
        
        # Remove duplicates and find the best container text (usually the one without SYNCING prefix)
        unique_texts = list(set(container_texts))
        best_container_text = None
        
        for text in unique_texts:
            if text and not text.startswith('SYNCING'):
                best_container_text = text
                break
        
        # If no text without SYNCING found, use the first available and remove SYNCING
        if not best_container_text and unique_texts:
            best_container_text = unique_texts[0]
            if best_container_text.startswith('SYNCING'):
                best_container_text = best_container_text[7:]
        
        if best_container_text:
            logging.debug(f"Processing best container text: '{best_container_text}'")
            
            # IGNORE the encoded format - it contains point values, not letter counts
            # Instead, we'll look for actual visible letter elements below
            logging.debug(f"Ignoring encoded container text (contains point values): '{best_container_text}'")
        
        # Also look for Game_letter__jIgKJ class which might contain individual letters
        game_letter_elements = soup.find_all(['div', 'span', 'button'], class_=re.compile(r'Game_letter'))
        logging.debug(f"Found {len(game_letter_elements)} game letter elements")
        
        for elem in game_letter_elements:
            text = elem.get_text().strip()
            if len(text) == 1 and text.isalpha():
                all_letters_found.append(text.upper())
                logging.debug(f"Found game letter: {text.upper()}")
            # Also check child elements
            child_letters = elem.find_all(['p', 'span'])
            for child in child_letters:
                child_text = child.get_text().strip()
                if len(child_text) == 1 and child_text.isalpha():
                    all_letters_found.append(child_text.upper())
                    logging.debug(f"Found child letter: {child_text.upper()}")
        
        # Look for any other letter containers we might have missed
        other_letter_containers = soup.find_all(['div', 'span', 'button'], 
                                               class_=re.compile(r'[Ll]etter|[Gg]ame.*[Ll]etter'))
        
        for container in other_letter_containers:
            text_content = container.get_text().strip()
            if len(text_content) == 1 and text_content.isalpha():
                all_letters_found.append(text_content.upper())
        
        # Now find completed words (for the big word tracking)
        word_slots = soup.find_all('div', class_=re.compile(r'Slot_slot'))
        
        for slot in word_slots:
            # Look for letter spans within each slot that form complete words
            letter_spans = slot.find_all('span', class_=re.compile(r'Slot_letter'))
            if letter_spans:
                # Extract letters and combine them into words
                letters = []
                for span in letter_spans:
                    p_tag = span.find('p')
                    if p_tag:
                        text = p_tag.get_text().strip()
                        if text and text != '.':
                            letters.append(text)
                
                if letters:
                    word = ''.join(letters).upper()
                    if word.isalpha() and len(word) >= 3:  # Only valid alphabetic words of 3+ letters
                        words.append(word)
                        logging.debug(f"Found game word: {word}")
        
        # Note: We only use the anagram container parsing above to avoid duplicates
        # The anagram container already contains all the scrambled letters we need
        
        # Update the global list of all letters (preserving duplicates for correct counts)
        if all_letters_found:
            # Keep all letters including duplicates, sorted for display
            sorted_letters = sorted(all_letters_found)
            update_all_letters(sorted_letters)
            logging.debug(f"Updated all letters: {', '.join(sorted_letters)} (total: {len(sorted_letters)})")
        
        # If no slots found, try alternative selectors for guessed words
        if not words:
            alternative_selectors = [
                ".guessed-words .word",
                "[class*='guessed'] [class*='word']",
                "[class*='word'][class*='guessed']"
            ]
            
            for selector in alternative_selectors:
                elements = soup.select(selector)
                if elements:
                    words = [w.get_text().strip().upper() for w in elements 
                            if w.get_text().strip() and w.get_text().strip().isalpha() and len(w.get_text().strip()) >= 3]
                    if words:
                        logging.debug(f"Found {len(words)} words using selector: {selector}")
                        break
        
        # Filter and clean words
        cleaned_words = []
        for word in words:
            cleaned_word = word.strip().upper()
            if cleaned_word and cleaned_word.isalpha() and len(cleaned_word) >= 3:
                cleaned_words.append(cleaned_word)
        
        logging.debug(f"Extracted {len(cleaned_words)} valid words")
        return cleaned_words
        
    except TimeoutException:
        logging.warning("Timeout waiting for page elements to load")
        return []
    except Exception as e:
        logging.error(f"Error extracting words from page: {e}")
        return []

def scrape_loop():
    """Main scraping loop that runs continuously"""
    logging.info("Starting scrape loop...")
    
    driver = setup_chrome_driver()
    if not driver:
        logging.error("Failed to set up Chrome driver, scraping will not work")
        return
    
    last_longest_word = ""
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    try:
        while True:
            try:
                logging.debug(f"Checking Words On Stream at {MIRROR_URL}")
                
                # Navigate to the page
                driver.get(MIRROR_URL)
                
                # Wait a bit for dynamic content to load
                time.sleep(3)
                
                # Extract words from the page
                words = extract_words_from_page(driver)
                
                if words:
                    # Find the longest word
                    longest_word = max(words, key=len)
                    
                    # Update big word if this is longer
                    if longest_word != last_longest_word:
                        if update_big_word(longest_word):
                            logging.info(f"New longest word found: {longest_word} (length: {len(longest_word)})")
                        last_longest_word = longest_word
                    
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                else:
                    logging.warning("No words found on the page")
                
            except WebDriverException as e:
                consecutive_errors += 1
                logging.error(f"WebDriver error (attempt {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("Too many consecutive WebDriver errors, restarting driver...")
                    try:
                        driver.quit()
                    except:
                        pass
                    
                    driver = setup_chrome_driver()
                    if not driver:
                        logging.error("Failed to restart Chrome driver, stopping scraper")
                        break
                    consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                logging.error(f"Unexpected error in scrape loop (attempt {consecutive_errors}): {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logging.error("Too many consecutive errors, stopping scraper")
                    break
            
            # Wait before next check
            logging.debug(f"Waiting {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Scrape loop interrupted by user")
    finally:
        if driver:
            try:
                driver.quit()
                logging.info("Chrome driver closed")
            except Exception as e:
                logging.error(f"Error closing Chrome driver: {e}")

if __name__ == "__main__":
    scrape_loop()
