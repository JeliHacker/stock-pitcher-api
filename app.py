from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import click
from flask.cli import with_appcontext


def safe_float(value, default=None):
    try:
        return float(value)
    except ValueError:
        return default


db = SQLAlchemy()


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    last_sale = db.Column(db.Float)
    net_change = db.Column(db.Float)
    percent_change = db.Column(db.String(10))
    market_cap = db.Column(db.String(20))
    country = db.Column(db.String(50))
    ipo_year = db.Column(db.Integer)
    volume = db.Column(db.Integer)
    sector = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    margin_of_safety = db.Column(db.Float)  # Assuming this is a percentage or float value
    business_predictability = db.Column(db.Integer)  # Assuming predictability is rated on an integer scale
    fair_value = db.Column(db.String(50))  # Storing as string due to potential currency symbols, but could be Float
    fair_value_minus_price = db.Column(db.Float)  # Assuming this is calculated as a float value
    baggers = db.Column(db.String(20))  # Assuming this might contain percentage symbols or other non-numeric characters

    def __repr__(self):
        return f'<Stock {self.symbol}>'


def import_stock_data(csv_file_path):
    print("import_stock_data()")
    df = pd.read_csv(csv_file_path)
    for index, row in df.iterrows():
        # Skip rows with missing or empty symbols
        if pd.isnull(row['Symbol']) or row['Symbol'].strip() == '':
            print(f"Skipping row {index} due to missing symbol.")
            continue

        stock = Stock(
            symbol=row['Symbol'],
            name=row['Name'],
            last_sale=safe_float(row['Last Sale']),
            net_change=safe_float(row['Net Change']),
            percent_change=row['% Change'],
            market_cap=row['Market Cap'],
            country=row['Country'] if 'Country' in row and pd.notnull(row['Country']) else '',
            ipo_year=int(row['IPO Year']) if 'IPO Year' in row and pd.notnull(row['IPO Year']) else None,
            volume=row['Volume'],
            sector=row['Sector'] if 'Sector' in row and pd.notnull(row['Sector']) else '',
            industry=row['Industry'] if 'Industry' in row and pd.notnull(row['Industry']) else '',
            margin_of_safety=safe_float(row['Margin of Safety']),
            business_predictability=row['Business Predictability'] if pd.notnull(
                row['Business Predictability']) else None,
            fair_value=row['Fair Value'] if pd.notnull(row['Fair Value']) else None,
            fair_value_minus_price=safe_float(row['Fair Value - Price']),
            baggers=row['Baggers'] if pd.notnull(row['Baggers']) else None
        )
        db.session.add(stock)
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def hello_world():
        return jsonify({'message': 'Hello, World!'})

    @app.route('/stocks')
    def get_stocks():
        stocks = Stock.query.limit(10).all()  # Fetch first 10 stocks
        stocks_data = []
        for stock in stocks:
            stocks_data.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'last_sale': stock.last_sale,
                'net_change': stock.net_change,
                'percent_change': stock.percent_change,
                'market_cap': stock.market_cap,
                'country': stock.country,
                'ipo_year': stock.ipo_year,
                'volume': stock.volume,
                'sector': stock.sector,
                'industry': stock.industry,
                'margin_of_safety': stock.margin_of_safety,
                'business_predictability': stock.business_predictability,
                'fair_value': stock.fair_value,
                'fair_value_minus_price': stock.fair_value_minus_price,
                'baggers': stock.baggers,
            })
        return jsonify(stocks_data)

    @app.cli.command('import-data')
    @click.argument('csv_file')
    @with_appcontext
    def import_data_command(csv_file):
        """Imports stock data from a CSV file."""
        import_stock_data(csv_file)
        click.echo(f'Data imported from {csv_file}')

    return app


app = create_app()


if __name__ == '__main__':
    print("main()")
    app.run(debug=True)

