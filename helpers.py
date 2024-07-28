import pandas as pd
import csv


def xlsx_to_csv(xlsx_file_path, csv_file_path):
    # Load the Excel file
    data = pd.read_excel(xlsx_file_path, engine='openpyxl')

    # Save to CSV
    data.to_csv(csv_file_path, index=False)


def read_csv(file_path):
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)
    return data


def write_to_txt(data, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for row in data:
            file.write(', '.join(row) + '\n')  # Keeping it comma-separated for simplicity


def convert_csv_to_txt(csv_file_path, txt_file_path):
    data = read_csv(csv_file_path)
    write_to_txt(data, txt_file_path)


if __name__ == "__main__":
    print("main()")
    convert_csv_to_txt("all_tickers.csv", "all_tickers.txt")
