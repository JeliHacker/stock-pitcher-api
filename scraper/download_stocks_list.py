from selenium.webdriver.common.by import By
import pandas as pd
import time
from scraper.scrape_all_stocks import create_driver
import shutil
import os
from glob import glob
import logging


def download_nasdaq_list(filename: str):
    """
    Downloads a full list of stocks (around 7,200 tickers as of 05/2024) from the Nasdaq website.
    This function creates a .csv file and .xlsx file.
    :param filename: What to name the list of stocks files (e.g. "stocks_list.csv")
    :return:
    """

    driver = create_driver()
    driver.get("https://www.nasdaq.com/market-activity/stocks/screener")
    time.sleep(5)
    driver.get_screenshot_as_file("screenshot.png")
    download_button = driver.find_element(By.CLASS_NAME, 'jupiter22-c-table__download-csv')
    download_button.click()
    time.sleep(5)

    # Use an environment variable if set, otherwise default to the user's Downloads folder
    downloads_folder = os.getenv('DOWNLOADS_FOLDER', os.path.expanduser('~/Downloads'))

    # Path to current directory
    project_directory = os.getcwd()

    # List all files in the Downloads folder
    files = glob(os.path.join(downloads_folder, '*'))

    # Find the most recently downloaded file (based on modification time)
    latest_file = max(files, key=os.path.getmtime)

    # Define destination directory (for example, an "archive" folder inside the project)
    destination_dir = os.path.join(project_directory, "archive")
    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)
    logging.info(f"project_directory/archive: {project_directory}/archive")

    # Construct the destination path. Here we assume 'filename' does NOT include a path.
    destination_path = os.path.join(destination_dir, f"{filename}.csv")

    # Move the most recently downloaded file to your project directory
    shutil.move(latest_file, os.path.join(f"{project_directory}", f"{filename}.csv"))

    df = pd.read_csv(f"{filename}.csv")
    excel_file_path = f"{filename}.xlsx"
    print(f"excel_file_path = {excel_file_path}")
    logging.info(f"excel_file_path = {excel_file_path}")
    df.to_excel(excel_file_path, index=False, engine="openpyxl", sheet_name="Stocks")
