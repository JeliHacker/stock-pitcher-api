# Stock Pitcher API

This API is for the Stock Pitcher mobile app. It hosts data I've scraped from the internet.

### Notes for the SEC API
The same category on two different annual reports may have different dictionary keys in the API. 
If one key doesn't return anything, try the other one.\
<ins>**Capital Expenditures**</ins>: PaymentsToAcquirePropertyPlantAndEquipment, PaymentsForCapitalImprovements\
<ins>**Cash Flow from Operations**</ins>: NetCashProvidedByUsedInOperatingActivities, NetCashProvidedByUsedInOperatingActivitiesContinuingOperations,\
<ins>**LongTermDebt**</ins>: LongTermDebt, LongTermDebtNoncurrent, LongTermDebtAndCapitalLeaseObligations\
<ins>**Revenue**</ins>: Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, SalesRevenueNet, SalesRevenueServicesNet

### Personal Notes
To update the SQLite database (stocks.db) run `flask import-data all_stocks_data.csv`. 
Note that the .csv file needs to be created by the DCF scraping function. You can use the `xlsx_to_csv` function helper here.  

### Ideas

You can get short interest data from the Nasdaq at pages like this:\
https://www.nasdaq.com/market-activity/stocks/pcb/short-interest

### Known Bugs
There is a problem with all_tickers.csv: some rows have too many commas which confuses the columns for the table and leads to issues.

### sec_api.py
The dates (x axis) should correspond to each filed 10-K