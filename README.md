# Stock Pitcher API

This API is for the Stock Pitcher mobile app. It hosts data I've scraped from the internet.

### Notes for the SEC API
The same category on two different annual reports may have different dictionary keys in the API. 
If one key doesn't return anything, try the other one.
Capital Expenditures: PaymentsToAcquirePropertyPlantAndEquipment, PaymentsForCapitalImprovements
cash flow from operations: NetCashProvidedByUsedInOperatingActivities, NetCashProvidedByUsedInOperatingActivitiesContinuingOperations, 
LongTermDebt: LongTermDebt, LongTermDebtNoncurrent, LongTermDebtAndCapitalLeaseObligations
Revenue: RevenueFromContractWithCustomerExcludingAssessedTax