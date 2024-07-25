import requests
import pandas as pd
from sec_api import HEADERS, get_cik_from_symbol, get_sp500_stocks, get_symbol_from_cik
from my_parse_345 import parse_345
import time
from datetime import datetime


# Define the function to get insider transactions
def get_insider_transactions(cik):
    """Get insider transactions for a single stock given a CIK number.
    This function doesn't do a whole lot, most of the work is in my_parse_345.py."""

    print(f"Getting insider transactions for {get_symbol_from_cik(cik)}")
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("response failed with code:", response.status_code)
        print("cik:", cik)
    data = response.json()

    # Initialize an empty DataFrame
    df = pd.DataFrame()

    # Filter for Forms 3, 4, and 5
    insider_forms = []

    # make a list of all Form 4s
    for i in range(len(data['filings']['recent']['form'])):
        if data['filings']['recent']['form'][i] in ['4']:  # look for specific form types
            current_filing = {}
            for key in data['filings']['recent'].keys():
                current_filing[key] = data['filings']['recent'][key][i]
            insider_forms.append(current_filing)

    for form in insider_forms:
        filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{form["accessionNumber"].replace("-", "")}/{form["primaryDocument"]}'

        # only get transactions going back to January 1st, 2020
        if datetime.strptime(form['filingDate'], '%Y-%m-%d') < datetime.strptime('2020-01-01', '%Y-%m-%d'):
            break

        # stay within SEC API rate limits (10 requests per second) ** citation needed **
        time.sleep(0.11)

        stock_data = parse_345(link=filing_url, cik=cik, filing_date=form['filingDate'])

        # if there is no data (because there is no insider buying, for example),
        # we do not want to combine the dataframes
        if stock_data.size > 0:
            df = pd.concat([df, stock_data], ignore_index=True)

    return df


# Define the function to determine buy/sell activity
def analyze_transactions(df):
    """This function currently does nothing."""
    # Simple logic to differentiate buy and sell (to be expanded based on actual filing content analysis)
    df['action'] = df['form'].apply(
        lambda x: 'buy' if '4' in x else 'unknown')  # Example, needs actual parsing of filing content
    return df


def iterate_through_database(input_file):
    df = pd.read_excel(f"{input_file}", sheet_name='Stocks')


# Main function to run the script
if __name__ == "__main__":
    # cik = get_cik_from_symbol('VFC', add_zeroes=True)
    # transactions_df = get_insider_transactions(cik)

    sp500_stocks = get_sp500_stocks()
    df = pd.DataFrame()
    for stock in sp500_stocks:
        new_df = get_insider_transactions(get_cik_from_symbol(stock['Symbol'], add_zeroes=True))
        df = pd.concat([df, new_df], ignore_index=True)

    df.to_excel('insider_buying.xlsx', index=False)
