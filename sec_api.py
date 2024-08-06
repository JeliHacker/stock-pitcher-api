# -*- coding: utf-8 -*-
"""

SEC Filing Scraper
@author: AdamGetbags

"""

# import modules
import requests
import pandas as pd
import matplotlib.pyplot as plt
import bs4
import os
from helpers import convert_csv_to_txt

# create request header
HEADERS = {'User-Agent': "eli@stockpitcher.app"}


def get_cik_from_symbol(stock_symbol, add_zeroes: bool = False):
    with open("all_tickers.txt", 'r') as file:
        for line in file:
            parts = line.strip().split(', ')
            if len(parts) >= 4 and parts[1] == stock_symbol:
                if add_zeroes:
                    return parts[2].zfill(10)
                else:
                    return parts[2]
    print("Error in get_cik_from_symbol. Could not find a CIK for that stock ticker.")
    return None


def get_symbol_from_cik(cik, csv_file_path='all_tickers.csv'):
    cik = str(cik).lstrip("0")

    with open("all_tickers.txt", 'r') as file:
        for line in file:
            parts = line.strip().split(', ')
            if len(parts) >= 4 and parts[2] == cik:
                return parts[1]
    print("Error in get_symbol_from_cik")
    return None  # Return None if no match is found


def get_all_tickers():
    # get all companies data
    company_tickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=HEADERS
    ).json()

    with open("all_tickers.csv", "w") as file:
        for key in company_tickers:
            curr = company_tickers[key]
            file.write(f"{key},{curr['ticker']},{curr['cik_str']},{curr['title']}\n")

    convert_csv_to_txt("all_tickers.csv", "all_tickers.txt")


def get_sp500_stocks():
    """This function returns a list of the current S&P 500 stock tickers,
    in alphabetical order."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'wikitable sortable'})

    # Iterate through the rows in the table and get data
    data = []
    rows = table.find_all('tr')
    for row in rows[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) > 1:  # If row isn't empty
            symbol = cols[0].text.strip()
            name = cols[1].text.strip()
            data.append({'Symbol': symbol, 'Security': name})

    print(data)
    return data


def get_filtered_values(data, key):
    print("get_filtered_values", key)
    if key in data['facts']['us-gaap']:
        try:
            values = data['facts']['us-gaap'][key]['units']['USD']
        except KeyError:
            return []
        return [entry for entry in values if entry.get('form') == '10-K']
    return []


def main(cik: str = None, ticker: str = None):
    # get company facts data
    company_facts = requests.get(
        f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
        headers=HEADERS
    ).json()

    # print(company_facts['facts']['us-gaap'].keys())
    # this code gets all the values for a given year and 10-K
    # helpful double-checking which dictionary keys correspond to whatever accounting items
    # for key in company_facts['facts']['us-gaap'].keys():
    #     try:
    #         category = company_facts['facts']['us-gaap'][key]['units']['USD']
    #         for dictionary in category:
    #
    #             if dictionary['form'] == '10-K' and dictionary['fy'] == 2023:
    #                 print(dictionary)
    #
    #                 print(key, dictionary['val'])
    #     except KeyError:
    #         print(f"key error for {key}")
    # return

    # for dictionary in company_facts['facts']['us-gaap']['LongTerm']['units']['USD']:
    #     print(dictionary)
    #     if dictionary['end'] == '2024-03-31':
    #         print(dictionary)
    # print("END")
    # return

    # Function to extract and filter data by form type (10-K)

    net_income_10k = get_filtered_values(company_facts, 'NetIncomeLoss')
    print("net_income_10k", net_income_10k)
    # Get cash flow from operations.
    cash_flow_operations_10k = get_filtered_values(company_facts, 'NetCashProvidedByUsedInOperatingActivities')

    # Get capital expenditures
    capital_expenditures_10k = get_filtered_values(company_facts, 'PaymentsToAcquirePropertyPlantAndEquipment')

    # Get acquisitions
    acquisitions_10k = get_filtered_values(company_facts, 'PaymentsToAcquireBusinessesNetOfCashAcquired')

    long_term_debt_10k = get_filtered_values(company_facts, 'LongTermDebtNoncurrent')

    stockholders_equity_10k = get_filtered_values(company_facts, 'StockholdersEquity')

    # Extract fiscal periods and values for each category
    def extract_periods_and_values(data, key=None):
        periods = [entry['end'] for entry in data if 'frame' in entry and len(entry['frame']) == 6] # len() == 6 fixes bug with net income
        values = [entry['val'] for entry in data if 'frame' in entry and len(entry['frame']) == 6]
        if key == 'net income':
            print("net income entries with frames below")
            print([entry for entry in data if 'frame' in entry])
        if key == 'debt':
            periods = [entry['end'] for entry in data if 'frame' in entry]
            values = [entry['val'] for entry in data if 'frame' in entry]
        if key == 'stockholders equity':
            seen_ends = set()
            for entry in data:
                if entry['end'] not in seen_ends:
                    seen_ends.add(entry['end'])
                    periods.append(entry['end'])
                    values.append(entry['val'])
        return periods, values

    # Extracting data
    fiscal_periods_income, net_income_values = extract_periods_and_values(net_income_10k, 'net income')
    fiscal_periods_cf, cash_flow_values = extract_periods_and_values(cash_flow_operations_10k)
    fiscal_periods_capex, capex_values = extract_periods_and_values(capital_expenditures_10k)
    fiscal_periods_acq, acq_values = extract_periods_and_values(acquisitions_10k)
    fiscal_periods_debt, debt_values = extract_periods_and_values(long_term_debt_10k, 'debt')
    fiscal_periods_stockholders_equity, stockholders_equity_values = extract_periods_and_values(stockholders_equity_10k, key='stockholders equity')

    for i in range(len(fiscal_periods_cf)):
        print("operating cash flows", fiscal_periods_cf[i], cash_flow_values[i])

    for i in range(len(fiscal_periods_capex)):
        print("capex:", fiscal_periods_capex[i], capex_values[i])

    for i in range(len(fiscal_periods_acq)):
        print("acquisitions:", fiscal_periods_acq[i], acq_values[i])

    for i in range(len(fiscal_periods_income)):
        print("net income:", fiscal_periods_income[i], net_income_values[i])

    for i in range(len(fiscal_periods_debt)):
        print("long-term debt:", fiscal_periods_debt[i], debt_values[i])

    for i in range(len(fiscal_periods_stockholders_equity)):
        print("long-term debt:", fiscal_periods_stockholders_equity[i], stockholders_equity_values[i])

    print(len(net_income_10k), len(long_term_debt_10k), len(capital_expenditures_10k), len(acquisitions_10k), len(cash_flow_operations_10k))

    # Plot the data
    plt.figure(figsize=(12, 8))

    # Plot cash flow from operations
    plt.plot(fiscal_periods_cf, cash_flow_values, marker='o', linestyle='-', color='b',
             label='Cash Flow from Operations')

    plt.plot(fiscal_periods_income, net_income_values, marker='o', linestyle='-', color='#5E6472',
             label='Net Income')

    # Plot capital expenditures
    plt.plot(fiscal_periods_capex, capex_values, marker='o', linestyle='-', color='r', label='Capital Expenditures')

    # Plot acquisitions
    plt.plot(fiscal_periods_acq, acq_values, marker='o', linestyle='-', color='g', label='Acquisitions')

    plt.plot(fiscal_periods_stockholders_equity, stockholders_equity_values, marker='o', linestyle='-', color='#FFC0CB',
             label='Stockholders Equity')

    plt.plot(fiscal_periods_debt, debt_values, marker='o', linestyle='-', color='#F1C646', label='Long-term Debt')

    plt.title(f'Financial Data for {ticker} (10-K)')
    plt.xlabel('Fiscal Period')
    plt.ylabel('USD')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


if __name__ == "__main__":
    TICKER = 'TITN'
    cik_value = get_cik_from_symbol(TICKER, add_zeroes=True)
    main(cik_value, ticker=TICKER)

