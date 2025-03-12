from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
import requests
import logging
import os
import platform


def create_driver():
    logging.info("create_driver()")
    print("create_driver()")
    options = Options()

    # Avoid detection as a bot
    options.add_argument("--disable-blink-features=AutomationControlled")

    # https://stackoverflow.com/questions/47316810/unable-to-locate-elements-on-webpage-with-headless-chrome
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options.add_argument(f'user-agent={user_agent}')

    # Essential flags for headless mode and stability
    options.add_argument('--headless=new')
    options.add_argument("--no-sandbox")  # Prevent sandbox issues (Linux)
    options.add_argument("--disable-dev-shm-usage")  # Fix crashes in headless mode
    options.add_argument("--disable-gpu")  # Helps on some headless setups
    options.add_argument("--window-size=1920x1080")  # Ensures elements are fully loaded

    downloads_folder = '/Users/eligooch/Downloads'

    if platform.system() == "Linux":  # VPS (Linux)
        options.binary_location = "/usr/bin/google-chrome"
        downloads_folder = os.getenv('DOWNLOADS_FOLDER', os.path.expanduser('~/Downloads'))

    # Configure Chromium to auto-download files without confirmation
    prefs = {
        "download.default_directory": downloads_folder,  # Set the default download folder
        "download.prompt_for_download": False,  # Disable the "Save As" dialog
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,  # Avoids warning prompts
        "safebrowsing.disable_download_protection": True,  # Allows auto-downloading
    }
    options.add_experimental_option("prefs", prefs)

    # Get the correct ChromeDriver path
    chrome_driver_dir = ChromeDriverManager().install()

    # Correct the path by replacing the incorrect file with actual binary
    if "THIRD_PARTY_NOTICES.chromedriver" in chrome_driver_dir:
        chrome_driver_dir = os.path.dirname(chrome_driver_dir) + "/chromedriver"

    print("Using ChromeDriver path:", chrome_driver_dir)

    service = Service(chrome_driver_dir)
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def scrape_data(driver, ticker: str):
    """
    This scrapes data from Gurufocus for each row. This is a subfunction to scrape_all_stocks.
    :param driver: the selenium webdriver
    :param ticker: the company's ticker symbol
    :return: a list [margin of safety, fair value, predictability stars]
    """
    print(f"scrape_data({ticker})")
    driver.get(f"https://www.gurufocus.com/stock/{ticker}/dcf")

    # Wait for the page to load sufficiently
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'dcf-result')))

    except TimeoutException:
        print(f"Timed out waiting for the page for {ticker} to load.")
        # Optionally, take a screenshot or dump the page source to help with debugging.
        # driver.save_screenshot('page_timeout.png')
        # with open('page_source.html', 'w') as f:
        #    f.write(driver.page_source)
        # Handle the exception or re-raise it if you want the script to stop here.
        return [-69420, -69420, -69420]

    percentage_text = 'Blank'
    predictability_stars = 0
    fair_value = 0

    # Implement a retry mechanism for BeautifulSoup
    attempts = 0
    timed_out = True
    while attempts < 4:
        attempts += 1
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')

        except WebDriverException as e:
            print("WebDriverException encountered:", e)
            return
            driver.quit()  # Quit the crashed driver
            time.sleep(5)  # Wait a bit before restarting
            driver = create_driver()  # Create a new driver instance
            continue

        if attempts > 1:
            print("Couldn't find margin of safety on first attempt. Trying again, slower this time")
            time.sleep(5)

        result_span = soup.find('span', class_='dcf-result')

        # Find the outermost div that contains the stars.
        outer_div = soup.find('div', class_='el-rate')

        if not result_span or not outer_div:
            continue

        # Get all elements with the class 'el-icon-star-on' within the outer div.
        stars = outer_div.find_all('i', class_='el-icon-star-on')

        # Filter full stars with the exact color style.
        full_stars = [star for star in stars if
                      'color:#F7BA2A;' in star.get('style', '') and not ('width:50%' in star.get('style', ''))]

        # Filter half stars with both the color and the width style.
        half_stars = [star for star in stars if
                      'color:#F7BA2A;' in star.get('style', '') and 'width:50%' in star.get('style', '')]

        predictability_stars = len(full_stars) + (0.5 * len(half_stars))

        price_div = soup.find('div', class_='fs-x-large fw-bolder text-right el-col el-col-12')
        fair_value = price_div.get_text(strip=True)

        if result_span:
            percentage_text = result_span.text.strip()
            timed_out = False
            break
        else:
            print(f"Retry {attempts + 1} for {ticker}")
            time.sleep(2)  # Wait a bit before retrying

    if timed_out:
        print(f"Failed to find margin of safety for {ticker} after {attempts} attempts.")
        return [percentage_text, predictability_stars, fair_value]

    if percentage_text == 'N/A':
        percentage_value = 'N/A'
    else:
        percentage_value = float(percentage_text.replace('%', '').replace(',', ''))

    return [percentage_value, predictability_stars, fair_value]


def scrape_all_stocks(input_file) -> bool:
    """
    Writes to the stocks list (which is the input file), adding 3 columns relating to fair value,
    based on data scraped from Gurufocus.
    :param input_file: Which file to read and write. This should be the relevant stocks list.
    :return: boolean: True if it got info for all the stocks in the Excel sheet
    """

    # Load the DataFrame
    df = pd.read_excel(f"{input_file}", sheet_name='Stocks')
    # Ensure the DataFrame has the necessary columns
    if 'Margin of Safety' not in df.columns:
        df['Margin of Safety'] = None
    if 'Business Predictability' not in df.columns:
        df['Business Predictability'] = None
    if 'Fair Value' not in df.columns:
        df['Fair Value'] = None

    try:
        driver = create_driver()
    except requests.exceptions.ReadTimeout as e:
        logging.error(f"ReadTimeout error: {e}")
        print("Getting a ReadTimeout error")
        raise

    processed_count = 0
    finished = True
    try:
        df['Symbol'] = df['Symbol'].str.replace('/', '.', regex=False)
        df['Symbol'] = df['Symbol'].str.replace('^', '.', regex=False)

        for index, row in df.iterrows():
            # Skip rows that have already been processed
            if pd.notna(row['Fair Value']):
                continue

            ticker = df['Symbol']
            attempt = 0
            data = None

            # Try twice
            while attempt < 2:
                try:
                    data = scrape_data(driver, row['Symbol'])
                    break
                except Exception as e:
                    attempt += 1
                    logging.error(f"Error processing ticker {row['Symbol']}: {e}", exc_info=True)
                    print(f"Error processing ticker {row['Symbol']}: {e}")
                    if attempt < 2:
                        # Restart driver before retrying
                        logging.info(f"Restarting driver and retrying ticker {ticker}")
                        driver.quit()
                        driver = create_driver()
                    else:
                        logging.error(f"Ticker {ticker} failed after {attempt} attempts. Skipping.")
                        print(f"Ticker {ticker} failed after {attempt} attempts. Skipping.")

                        continue

            print(f"{row['Symbol']}: {data}, stocks processed: {processed_count}")
            logging.info(f"{row['Symbol']}: {data}, stocks processed: {processed_count}")
            if data:
                mos = data[0]
                if mos == 'N/A':
                    mos = np.nan

                stars = data[1]
                if stars == 'N/A':
                    stars = np.nan

                fair_value = data[2]
                if fair_value == 'N/A':
                    fair_value = np.nan

                df.at[index, 'Margin of Safety'] = mos
                df.at[index, 'Business Predictability'] = stars
                df.at[index, 'Fair Value'] = fair_value

            processed_count += 1

            if processed_count >= 10:
                finished = False
                print("trying to copy to Excel", input_file)
                logging.info(f"trying to copy to Excel {input_file}")
                df.to_excel(f"{input_file}", sheet_name='Stocks', index=False)
                break
    except Exception as e:
        logging.error("Error occurred", exc_info=True)
    finally:
        driver.quit()
        df.to_excel(f"{input_file}", sheet_name='Stocks', index=False)
        logging.info(f"Updated {input_file} ~ scrape_all_stocks.py")
        return finished


if __name__ == "__main__":
    print(platform.system())
    print("scrape_all_stocks.py")
