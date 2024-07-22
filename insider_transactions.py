import requests
import pandas as pd
from sec_api import HEADERS, get_cik_from_symbol
from my_parse_345 import parse_345
import time
from datetime import datetime


# Define the function to get insider transactions
def get_insider_transactions(cik):
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print("response failed with code:", response.status_code)
        print("cik:", cik)
    data = response.json()

    # Filter for Forms 3, 4, and 5
    insider_forms = []

    for i in range(len(data['filings']['recent']['form'])):
        if data['filings']['recent']['form'][i] in ['4']: # look for specific form types
            current_filing = {}
            for key in data['filings']['recent'].keys():
                current_filing[key] = data['filings']['recent'][key][i]
            insider_forms.append(current_filing)

    transactions = []
    for form in insider_forms:
        filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{form["accessionNumber"].replace("-", "")}/{form["primaryDocument"]}'

        if datetime.strptime(form['filingDate'], '%Y-%m-%d') < datetime.strptime('2020-01-01', '%Y-%m-%d'):
            break

        filer = parse_345(filing_url, form['filingDate'])
        time.sleep(0.11)
        # print("-- PARSING -- ")

        transactions.append({
            'form': form['form'],
            'filing_date': form['filingDate'],
            'document_url': filing_url
        })

    return pd.DataFrame(transactions)


# Define the function to determine buy/sell activity
def analyze_transactions(df):
    # Simple logic to differentiate buy and sell (to be expanded based on actual filing content analysis)
    df['action'] = df['form'].apply(
        lambda x: 'buy' if '4' in x else 'unknown')  # Example, needs actual parsing of filing content
    return df


# Main function to run the script
if __name__ == "__main__":
    cik = get_cik_from_symbol('VFC', add_zeroes=True)
    transactions_df = get_insider_transactions(cik)
    # analyzed_df = analyze_transactions(transactions_df)

    # print(analyzed_df)
