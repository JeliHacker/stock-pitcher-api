from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import click
from flask.cli import with_appcontext
import sqlite3
from celery import Celery
from redis import Redis


def make_celery(app_input):
    celery_component = Celery(app_input.import_name, broker=app_input.config['CELERY_broker_url'])
    celery_component.conf.update(app_input.config)
    celery_component.autodiscover_tasks(force=True)
    return celery_component


def clean_currency(value):
    """Remove dollar signs and commas and convert to float, handle both strings and floats."""
    if isinstance(value, float):  # If it's already a float, return it as is
        return value
    if isinstance(value, str):  # If it's a string, clean it up
        return float(value.replace('$', '').replace(',', ''))
    raise ValueError(f"Unexpected data type: {type(value)}")


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
    margin_of_safety = db.Column(db.Float)
    business_predictability = db.Column(db.Integer)  # Business Predictability is on a scale of 1-5
    fair_value = db.Column(db.Float)  # Storing as string due to potential currency symbols, but could be Float
    fair_value_minus_price = db.Column(db.Float)
    baggers = db.Column(db.Float)  # Baggers is fair_value_minus_price divided by price

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
            fair_value=clean_currency(row['Fair Value']) if pd.notnull(row['Fair Value']) else None,
            fair_value_minus_price=safe_float(row['Fair Value - Price']),
            baggers=clean_currency(row['Baggers']) if pd.notnull(row['Baggers']) else None
        )
        db.session.add(stock)
    db.session.commit()


def get_db_connection():
    # Connection setup to your SQLite database
    conn = sqlite3.connect('instance/stocks.db')
    conn.row_factory = sqlite3.Row
    return conn


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CELERY_broker_url'] = 'redis://localhost:6379/0'
    app.config['result_backend'] = 'redis://localhost:6379/0'

    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route('/')
    def hello_world():
        return jsonify({'message': 'Welcome to the Stock Pitcher API!'
                                   ' I created this API to use in my Stock Pitcher mobile app.'
                                   ' It delivers stock data that comes from the Nasdaq website and Gurufocus.'})

    @app.route('/stocks')
    def get_stocks():
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=50, type=int)
        offset = (page - 1) * limit

        # Assuming you have a database connection function
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stock ORDER BY baggers DESC LIMIT ? OFFSET ?', (limit, offset))
        stocks = cursor.fetchall()
        conn.close()

        return jsonify([dict(stock) for stock in stocks])

    @app.route('/stocks/<string:ticker>')
    def get_stock(ticker):
        stock = Stock.query.filter_by(symbol=ticker.upper()).first()
        if stock:
            return jsonify({
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
                'baggers': stock.baggers
            })
        else:
            abort(404)  # Not found if there's no stock with the given symbol

    @app.route('/add/<int:a>/<int:b>')
    def add(a, b):
        task = add_together.delay(a, b)
        return str(task.get(timeout=30))  # Using timeout to simulate waiting for result

    @app.cli.command('import-data')
    @click.argument('csv_file')
    @with_appcontext
    def import_data_command(csv_file):
        """Imports stock data from a CSV file."""
        import_stock_data(csv_file)
        click.echo(f'Data imported from {csv_file}')

    return app


app = create_app()

celery = make_celery(app)


@celery.task(name='add_together')
def add_together(a, b):
    return a + b


if __name__ == '__main__':
    print("main()")
    app.run(debug=True)

