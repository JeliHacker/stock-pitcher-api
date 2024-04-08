import pandas as pd


def xlsx_to_csv(xlsx_file_path, csv_file_path):
    # Load the Excel file
    df = pd.read_excel(xlsx_file_path, engine='openpyxl')

    # Save to CSV
    df.to_csv(csv_file_path, index=False)


# Example usage
xlsx_file_path = 'all_stocks_data.xlsx'
csv_file_path = 'all_stocks_data.csv'
xlsx_to_csv(xlsx_file_path, csv_file_path)
