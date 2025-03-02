from download_stocks_list import download_nasdaq_list
from scrape_all_stocks import scrape_all_stocks
import datetime
import os
import requests
import time
import logging

LOG_FILE = os.getenv("STOCK_API_SCRAPER_LOG_FILE", "logs/main.log")


# Ensure the directory exists
log_dir = os.path.dirname(LOG_FILE)
if log_dir and not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("main.py is running baby!")


def main():
    print("main()")
    current_date = datetime.datetime.now().strftime("%m_%d_%Y")  # Formats date as MM_DD_YYYY
    master_filename = f"archive/stocks_list_{current_date}" # e.g. stocks_list_05_12_2024

    if not os.path.exists(f"{master_filename}.xlsx"):
        download_nasdaq_list(master_filename)

    done = False
    count = 0
    attempt = 0
    max_retries = 3
    while not done and attempt < max_retries:
        print("NOT DONE! count:", count)
        try:
            done = scrape_all_stocks(f"{master_filename}.xlsx")
            attempt = 0
        except requests.exceptions.ReadTimeout:
            logging.warning(f"Retrying in 5 seconds...")
            time.sleep(5)
            attempt += 1

        count += 1

    if done:
        print("STATUS: Done")
        logging.info("STATUS: Done")


if __name__ == "__main__":
    main()
