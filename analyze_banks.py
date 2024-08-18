from sec_api import HEADERS, get_cik_from_symbol, get_all_tickers
import requests
import pandas as pd
import yfinance as yf
import locale

# TODO : fix bug where some shares outstanding don't have the last three zeros
# i.e. shares outstanding is 17829 when it should be 17829000

# Set the locale to US English
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Define ANSI escape codes for styling
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


def format_currency(value):
    return locale.currency(value, grouping=True)


def get_stock_price_yahoo(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period='1d')
    latest_price = data['Close'].iloc[-1]
    return latest_price


def analyze_banks():
    df = pd.read_excel('bank_data.xlsx')
    results = []

    count = 0
    for index, row in df.iterrows():
        if row['Country'] != "United States":
            continue

        ticker = row['Symbol']
        print(f"{BOLD}{UNDERLINE}{ticker}{END}")

        cik = get_cik_from_symbol(ticker, add_zeroes=True)
        if not cik:
            continue
        try:
            company_facts = requests.get(
                f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json',
                headers=HEADERS
            )
            if company_facts.status_code == 404:
                continue
            company_facts = company_facts.json()

            try:
                price = get_stock_price_yahoo(ticker)
            except IndexError:
                print(f"Error getting price for {ticker}.")
                continue

            stockholders_equity = company_facts['facts']['us-gaap']['StockholdersEquity']['units']['USD'][-1]['val']
            # shares_outstanding = company_facts['facts']['dei']['EntityCommonStockSharesOutstanding']['units']['shares'][-1]['val']
            shares_outstanding = company_facts['facts']['us-gaap']['WeightedAverageNumberOfSharesOutstandingBasic']['units']['shares'][-1]['val']
            market_cap = shares_outstanding * price
            pb_ratio = market_cap / stockholders_equity

            # Round the P/B ratio to 3 decimal places
            pb_ratio = round(pb_ratio, 3)

            print(f"stockholders equity: {format_currency(stockholders_equity)},\n"
                  f"stock price: {format_currency(price)},\n"
                  f"shares outstanding: {shares_outstanding},\n"
                  f"market cap: {format_currency(shares_outstanding * price)}\n"
                  f"book value / market cap (P/B): {BOLD}{UNDERLINE}{format_currency((shares_outstanding * price)/stockholders_equity)}{END}")

            results.append({'Ticker': ticker, 'P/B Ratio': pb_ratio})
        except KeyError:
            print(f"{BOLD}{UNDERLINE}{ticker}{END} has a KeyError")
            continue

    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv('bank_analysis.csv', index=False)
    print("Results saved to bank_analysis.csv")


analyze_banks()
