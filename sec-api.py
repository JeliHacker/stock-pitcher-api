# -*- coding: utf-8 -*-
"""

SEC Filing Scraper
@author: AdamGetbags

"""

# import modules
import requests
import pandas as pd
import matplotlib.pyplot as plt

# create request header
headers = {'User-Agent': "eli@stockpitcher.app"}


def find_cik_for_ticker(ticker: str):
    company_tickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
    ).json()



def get_all_tickers():
    # get all companies data
    company_tickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
    ).json()

    with open("all_tickers.csv", "w") as file:
        for key in company_tickers:
            curr = company_tickers[key]
            file.write(f"{key},{curr['ticker']},{curr['cik_str']},{curr['title']}\n")


def main(cik: str = None):
    print("main")


    # get all companies data
    companyTickers = requests.get(
        "https://www.sec.gov/files/company_tickers.json",
        headers=headers
    ).json()

    # dictionary to dataframe
    companyData = pd.DataFrame.from_dict(companyTickers,
                                         orient='index')

    # add leading zeros to CIK
    companyData['cik_str'] = companyData['cik_str'].astype(
                               str).str.zfill(10)

    if not cik:
        cik = companyData.iloc[2833]['cik_str']

    print("cik =", cik, type(cik))
    # get company facts data
    company_facts = requests.get(
        f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
        headers=headers
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
    def get_filtered_values(data, key):
        if key in data['facts']['us-gaap']:
            values = data['facts']['us-gaap'][key]['units']['USD']
            return [entry for entry in values if entry.get('form') == '10-K']
        return []

    # Get cash flow from operations.
    cash_flow_operations_10k = get_filtered_values(company_facts, 'NetCashProvidedByUsedInOperatingActivities')

    # Get capital expenditures
    capital_expenditures_10k = get_filtered_values(company_facts, 'PaymentsToAcquirePropertyPlantAndEquipment')

    print("capital expenditures: ", capital_expenditures_10k)
    # Get acquisitions
    acquisitions_10k = get_filtered_values(company_facts, 'LongTermDebtNoncurrent')

    # Extract fiscal periods and values for each category
    def extract_periods_and_values(data):
        periods = [entry['end'] for entry in data if 'frame' in entry]
        values = [entry['val'] for entry in data if 'frame' in entry]
        return periods, values

    # Extracting data
    fiscal_periods_cf, cash_flow_values = extract_periods_and_values(cash_flow_operations_10k)
    fiscal_periods_capex, capex_values = extract_periods_and_values(capital_expenditures_10k)
    fiscal_periods_acq, acq_values = extract_periods_and_values(acquisitions_10k)

    for i in range(len(fiscal_periods_cf)):
        print("operating cash flows", fiscal_periods_cf[i], cash_flow_values[i])

    for i in range(len(fiscal_periods_capex)):
        print("capex:", fiscal_periods_capex[i], capex_values[i])

    for i in range(len(fiscal_periods_acq)):
        print("debt:", fiscal_periods_acq[i], acq_values[i])

    print(fiscal_periods_capex)
    # Plot the datag
    plt.figure(figsize=(12, 8))

    # Plot cash flow from operations
    plt.plot(fiscal_periods_cf, cash_flow_values, marker='o', linestyle='-', color='b',
             label='Cash Flow from Operations')

    # Plot capital expenditures
    plt.plot(fiscal_periods_capex, capex_values, marker='o', linestyle='-', color='r', label='Capital Expenditures')

    # Plot acquisitions
    plt.plot(fiscal_periods_acq, acq_values, marker='o', linestyle='-', color='g', label='Acquisitions')

    plt.title('Financial Data for AMC Networks Inc. (10-K)')
    plt.xlabel('Fiscal Period')
    plt.ylabel('USD')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


main("1609711".zfill(10))
