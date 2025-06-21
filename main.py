import logging
from threading import Thread
from app import app
from scraper import scrape_loop

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def start_background_scraper():
    """Start the background scraper thread"""
    logging.info("Starting background scraper thread...")
    scraper_thread = Thread(target=scrape_loop, daemon=True)
    scraper_thread.start()
    logging.info("Background scraper thread started successfully")

# Start scraper in the background when module is imported
start_background_scraper()
