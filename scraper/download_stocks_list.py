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
    api_url = "https://api.nasdaq.com/api/screener/stocks?limit=10000&tableonly=true&download=true"

    # Keeping it simple bypasses errors for some reason
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

    # Drop the 'url' column if present
    if "url" in df.columns:
        df.drop(columns=["url"], inplace=True)

    # Rename columns
    rename_map = {
        "symbol": "Symbol",
        "name": "Name",
        "lastsale": "Last Sale",
        "netchange": "Net Change",
        "pctchange": "% Change",
        "volume": "Volume",
        "marketCap": "Market Cap",
        "country": "Country",
        "ipoyear": "IPO Year",
        "industry": "Industry",
        "sector": "Sector"
    }
    df.rename(columns=rename_map, inplace=True)

    # Reorder columns to match your desired sequence
    desired_order = [
        "Symbol",
        "Name",
        "Last Sale",
        "Net Change",
        "% Change",
        "Market Cap",
        "Country",
        "IPO Year",
        "Volume",
        "Sector",
        "Industry",
    ]
    # Filter to only columns that exist, in case some are missing
    existing_cols_in_order = [col for col in desired_order if col in df.columns]
    df = df[existing_cols_in_order]

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
