import requests
import sys
import os
import pandas as pd
from sec_api import (HEADERS, get_cik_from_symbol, get_sp500_stocks,
                     get_symbol_from_cik, get_all_tickers)
from my_parse_345 import parse_345
import time
from datetime import datetime
import json


# Append the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '')))
get_all_tickers()

current_date = datetime.now().strftime('%Y-%m-%d')


# Define the function to get insider transactions
def get_insider_transactions(cik, to_date='2020-01-01'):
    """Get insider transactions for a single stock given a CIK number.
    This function doesn't do a whole lot, most of the work is in my_parse_345.py.
    :param cik
    :param to_date"""

    # remove the leading zeroes so the sym_so
    cik_remove_leading_zeroes = cik.lstrip("0")
    print(f"Getting insider transactions for {get_symbol_from_cik(cik_remove_leading_zeroes, '../all_tickers.csv')}, "
          f"going back to date {to_date}")
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
        if datetime.strptime(form['filingDate'], '%Y-%m-%d') < datetime.strptime(to_date, '%Y-%m-%d'):
            print(f"{datetime.strptime(form['filingDate'], '%Y-%m-%d')} is less than {datetime.strptime(to_date, '%Y-%m-%d')}")
            break
        else:
            print(
                f"{datetime.strptime(form['filingDate'], '%Y-%m-%d')} is > or equal to {datetime.strptime(to_date, '%Y-%m-%d')}")

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
    # sp500_stocks = get_sp500_stocks()
    # try:
    #     with open('sp500_list.json', 'r') as file:
    #         old_list = json.load(file)
    #         if old_list != sp500_stocks:
    #             print("There's been an update to the S&P 500!")
    # except FileNotFoundError:
    #     print("No existing sp500_list.json file.")
    #
    # if os.path.exists('insider_buying.xlsx'):
    #     df = pd.read_excel('insider_buying.xlsx')
    # else:
    #     df = pd.DataFrame()
    #
    # with open('sp500_list_seen.json', 'r') as file:
    #     seen_stocks = json.load(file)
    #     print("type(seen_stocks)", type(seen_stocks))
    #
    # count = 0
    # for stock in seen_stocks:
    #     print(stock)
    #     if 'Last Scraped' in stock and stock['Last Scraped'] == current_date:
    #         print(f"This stock, {stock['Symbol']}, has been scraped before!")
    #         if stock['Last Scraped'] == current_date:
    #             print(f"skipping {stock['Symbol']} because we scraped it today, {stock['Last Scraped']}.")
    #
    #         continue
    #
    #     new_df = get_insider_transactions(cik=get_cik_from_symbol(stock['Symbol'], add_zeroes=True),
    #                                       to_date=stock.get('Last Scraped', '2020-01-01'))
    #     df = pd.concat([df, new_df], ignore_index=True)
    #     df.to_excel('insider_buying.xlsx', index=False)
    #
    #     stock['Last Scraped'] = current_date
    #     count += 1
    #
    #     if count > 0:
    #         break
    #
    # with open("sp500_list_seen.json", 'w') as file:
    #     json.dump(seen_stocks, file, indent=4)

    df = get_insider_transactions(cik=get_cik_from_symbol('CNH', add_zeroes=True), to_date='2022-01-01')

    df.to_excel('CNH_insider_buying.xlsx', index=False)


