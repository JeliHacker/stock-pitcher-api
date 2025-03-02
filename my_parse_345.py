import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re
import numpy as np
from sec_api import HEADERS, get_symbol_from_cik
import os


def clean_currency(value, safe_mode=True):
    """Remove dollar signs and commas and convert to float, handle both strings and floats.
    :param value:
    :param safe_mode when safe_mode is true the function will return 0 if the input is blank.
    When safe_mode is false the function will throw an error if the input is blank."""
    if isinstance(value, float):  # If it's already a float, return it as is
        return value
    if isinstance(value, str):  # If it's a string, clean it up
        # Remove contents within parentheses along with the parentheses themselves
        value = re.sub(r'\([^)]*\)', '', value)
        value = value.replace('$', '').replace(',', '')
        if safe_mode and (not value or value.strip() == ""):
            return float(0)
        return float(value)
    raise ValueError(f"Unexpected data type: {type(value)}")


def format_price(price_str):
    # Remove the footnote in parentheses
    price_without_footnote = re.sub(r'\(.*?\)', '', price_str)

    # Convert to float and format to two decimal places
    price_float = float(price_without_footnote.replace('$', ''))
    formatted_price = f"${price_float:.2f}"

    return formatted_price


def reformat_name(name):
    # Split the name into parts
    name_parts = name.split()
    # Move the last name (first part) to the end
    reformatted_name = ' '.join(name_parts[1:] + [name_parts[0]])
    return reformatted_name


def parse_345(link: str, cik, filing_date=None):
    """This is the main parsing function.
    Right now it's really only useful for identifying if a form describes insider buying
    and getting good data from it."""
    form_data = {}
    filer = None
    stock_price = None

    html_content = requests.get(link, headers=HEADERS).content
    soup = bs(html_content, "html.parser")

    # Find the specific table
    table = soup.find("table", {"width": "100%", "border": "1", "cellspacing": "0", "cellpadding": "4"})

    rows = soup.find_all("tr")

    buying_rows = []
    for row in rows:
        columns = row.find_all("td")
        if len(columns) > 7:
            security_type = columns[0].text.strip()
            transaction_code = columns[3].text.strip()
            transaction_type = columns[6].text.strip()

            if security_type == "Common Stock" and transaction_code == "P" and transaction_type == "A":
                # print("Someone is buying!:", link)
                buying_rows.append(row)

    # Extract the name from the nested table
    if table:
        name_link = table.find("a", href=True)
        if name_link:
            filer = name_link.text.strip()

    rows = soup.find_all("tr")

    buying_rows = []
    for row in rows:

        columns = row.find_all("td")
        if len(columns) > 10:
            try:
                amount_of_shares = float(columns[5].text.strip().replace(",", ""))
            except ValueError:
                continue

            # Date that comes straight from the form
            security_type = columns[0].text.strip()
            transaction_date = columns[1].text.strip()
            deemed_execution_date = columns[2].text.strip()
            transaction_code = columns[3].text.strip()
            transaction_code_v = columns[4].text.strip()
            amount_of_shares = float(columns[5].text.strip().replace(",", ""))  # amount of shares acquired or disposed
            a_or_d = columns[6].text.strip()  # "Securities Acquired (A) or Disposed Of (D)"
            stock_price = clean_currency(columns[7].text.strip().replace(",", ""))
            amount_of_securities_owned_following_transaction = clean_currency(columns[8].text.strip().replace(",", ""))
            ownership_form = columns[9].text.strip()  # Direct (D) or Indirect (I)
            nature_of_indirect_beneficial_ownership = columns[10].text.strip()

            if security_type == "Common Stock" and transaction_code == "P" and a_or_d == "A":
                # New data that we calculate
                amount_before_transaction = amount_of_securities_owned_following_transaction - amount_of_shares

                try:
                    percent_increase_in_shares = ((amount_of_securities_owned_following_transaction - amount_before_transaction) /
                                                  amount_before_transaction) * 100
                except ZeroDivisionError:
                    # BUG2FIX - https://www.sec.gov/Archives/edgar/data/103379/000112760223027261/xslF345X05/form4.xml
                    # for filing like these ^^^ we need to
                    # correctly identify the amount of shares owned following transaction.
                    # This is a problem for a lot of files. Here's another example:
                    # https://www.sec.gov/Archives/edgar/data/66740/000112760223026323/xslF345X05/form4.xml
                    print(f"ZeroDivisionError | "
                          f"amount_of_securities_owned_following_transaction: "
                          f"{amount_of_securities_owned_following_transaction},"
                          f"amount_before_transaction: {amount_before_transaction}")
                    percent_increase_in_shares = 100

                money_invested = amount_of_shares * stock_price

                with open("data.txt", "w") as file:
                    i = 0
                    for column in columns:
                        file.writelines(f"column {i}: {column.text.strip()}\n\n")
                        i += 1
                    file.writelines(f"amount_before_transaction: {amount_before_transaction}\n")
                    file.writelines(f"percent_increase_in_shares: {percent_increase_in_shares}\n")
                    file.writelines(f"money_invested: {money_invested}\n")

                stock_price = format_price(str(stock_price))  # e.g. $28.0407(1) -> $28.04
                print(f"Someone is buying! {reformat_name(filer)}, at a price of {stock_price}, on {filing_date} {link}")
                buying_rows.append(row)
                form_data = {
                    'Ticker': get_symbol_from_cik(cik.lstrip("0"), csv_file_path='../all_tickers.csv'),
                    'Date': transaction_date,
                    'Reporting Person': reformat_name(filer),
                    'Shares Bought': amount_of_shares,
                    'Price': stock_price,
                    'Cash Spent': money_invested,
                    'Percent Increase in Shares': round(percent_increase_in_shares, 2)
                }

    return pd.DataFrame([form_data])
