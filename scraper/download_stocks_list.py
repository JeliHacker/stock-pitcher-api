import pandas as pd
import logging
import requests


def download_nasdaq_list(filename: str):
    """
    Downloads a full list of stocks (around 7,200 tickers as of 05/2024) from the Nasdaq website.
    This function creates a .csv file and .xlsx file.
    :param filename: What to name the list of stocks files (e.g. "stocks_list.csv")
    :return:
    """
    print("download_nasdaq_list()")
    # API endpoint
    api_url = "https://api.nasdaq.com/api/screener/stocks?limit=50&tableonly=true&download=true"

    # Nasdaq often expects certain headers. These mimic a typical browser request.
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # Fetch data from the API
    response = requests.get(api_url, headers=headers, timeout=15)
    response.raise_for_status()  # Raise an error for a bad status code
    json_data = response.json()

    # Ensure we got the expected data structure
    if "data" not in json_data:
        raise ValueError("Unexpected API response: missing 'data' key")

    # Extract the rows of stocks
    rows = json_data["data"].get("rows", [])
    if not rows:
        raise ValueError("No stock data found in API response")

    # Create a DataFrame from the rows
    df = pd.DataFrame(rows)

    # Define output file names
    csv_file = f"{filename}.csv"
    excel_file = f"{filename}.xlsx"

    # Save DataFrame to CSV
    df.to_csv(csv_file, index=False)
    logging.info(f"Saved CSV to {csv_file}")

    # Save DataFrame to Excel
    df.to_excel(excel_file, index=False, engine="openpyxl", sheet_name="Stocks")
    logging.info(f"Saved Excel to {excel_file}")

    print(f"Successfully saved CSV to {csv_file} and Excel to {excel_file}")
