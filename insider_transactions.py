import requests
import pandas as pd
from sec_api import HEADERS, get_cik_from_symbol


# Define the function to get insider transactions
def get_insider_transactions(cik):
    url = f'https://data.sec.gov/submissions/CIK{cik}.json'
    response = requests.get(url, headers=HEADERS)
    print(response.status_code)
    data = response.json()

    # Filter for Forms 3, 4, and 5
    insider_forms = []

    for i in range(len(data['filings']['recent']['form'])):
        if data['filings']['recent']['form'][i] in ['3', '4', '5']:
            print(i, data['filings']['recent']['form'][i], data['filings']['recent']['reportDate'][i])
            current_filing = {}
            for key in data['filings']['recent'].keys():
                current_filing[key] = data['filings']['recent'][key][i]
            insider_forms.append(current_filing)

    with open('dict.txt', 'w') as file:
        for form in insider_forms:
            file.writelines(f"{form}\n")

    transactions = []
    for form in insider_forms[:5]:
        filing_url = f'https://www.sec.gov/Archives/edgar/data/{cik}/{form["accessionNumber"].replace("-", "")}/{form["primaryDocument"]}'

        filing_response = requests.get(filing_url, headers=HEADERS)
        print('filing_url', filing_url, filing_response)
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
    cik = get_cik_from_symbol('all_tickers.txt', 'VFC', add_zeroes=True)  # Example CIK for Apple Inc.
    transactions_df = get_insider_transactions(cik)
    analyzed_df = analyze_transactions(transactions_df)

    print(analyzed_df)
