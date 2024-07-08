import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import re
import numpy as np
from sec_api import HEADERS


def parse_345(link):
    form_data = {}

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
                print("Someone is buying!:", link)
                buying_rows.append(row)

    # Extract the name from the nested table
    if table:
        name_link = table.find("a", href=True)
        if name_link:
            return name_link.text.strip()

    return None
