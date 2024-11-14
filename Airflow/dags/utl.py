# Code by Utkarsh Tripathi (017855552) and Leela Prasad (018210452)
from airflow import DAG
from airflow.models import Variable
from airflow.decorators import task
from datetime import timedelta, datetime
import pandas as pd
import requests
import snowflake.connector

# Function to get Snowflake connection
def return_snowflake_conn():
    user_id = Variable.get('Snowflake_UserName')
    password = Variable.get('Snowflake_Password')
    account = Variable.get('Snowflake_Account')
    # Establish a connection to Snowflake
    conn = snowflake.connector.connect(
        user=user_id,
        password=password,
        account=account,
        warehouse='compute_wh',
        database='lab2_work',
        schema='raw_data_lab2'
    )
    return conn

# Default arguments for the DAG
default_args = {
    'owner': 'Utkarsh Tripathi',
    'depends_on_past': False,
    'email_on_failure': ['tripathiutkarsh46@gmail.com'],
    'email_on_retry': ['tripathiutkarsh46@gmail.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    dag_id='Stock_data_analysis_lab2utl',
    default_args=default_args,
    description='A DAG to fetch stock prices and insert into Snowflake',
    schedule='00 17 * * *',
    start_date=datetime(2024, 10, 10),
    catchup=False
) as dag:

    @task()
    def extract(symbols):
        """Extract the last 90 days of stock prices for multiple symbols and return a single DataFrame."""
        vantage_api_key = Variable.get('API_Key')
        all_data = []  # Initialize an empty list to store data for both symbols

        for symbol in symbols:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={vantage_api_key}"
            r = requests.get(url)
            data = r.json()

            # Retrieve time series data
            time_series = data.get("Time Series (Daily)", {})
            date_list = sorted(time_series.keys())[-90:]  # Get the last 90 days

            # Append data for each symbol
            for date in date_list:
                daily_data = time_series[date]
                all_data.append({
                    "date": date,
                    "open": float(daily_data["1. open"]),
                    "high": float(daily_data["2. high"]),
                    "low": float(daily_data["3. low"]),
                    "close": float(daily_data["4. close"]),
                    "volume": int(daily_data["5. volume"]),
                    "symbol": symbol
                })

        # Create a DataFrame from the combined data for all symbols
        df = pd.DataFrame(all_data)
        return df  # Return the combined DataFrame

    @task()
    def create_stock_prices_table():
        """Create the stock prices table in Snowflake."""
        conn = return_snowflake_conn()
        curr = conn.cursor()

        create_table_query = """
            CREATE OR REPLACE TABLE lab2_work.raw_data_lab2.stock_prices_symbols (
                date DATE PRIMARY KEY,
                open FLOAT,
                high FLOAT,
                low FLOAT,
                close FLOAT,
                volume INTEGER,
                symbol VARCHAR
            );
        """
        try:
            curr.execute(create_table_query)
            print("Table created successfully.")
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            curr.close()
            conn.close()

    @task()
    def insert_stock_prices(df_data):
        """Insert stock data into the Snowflake table ensuring idempotency."""
        conn = return_snowflake_conn()
        curr = conn.cursor()

        df = pd.DataFrame(df_data)
        merge_query = """
        MERGE INTO lab2_work.raw_data_lab2.stock_prices_symbols AS target
        USING (SELECT %s AS date, %s AS open, %s AS high, %s AS low, %s AS close, %s AS volume, %s AS symbol) AS source
        ON target.date = source.date AND target.symbol = source.symbol
        WHEN NOT MATCHED THEN
            INSERT (date, open, high, low, close, volume, symbol)
            VALUES (source.date, source.open, source.high, source.low, source.close, source.volume, source.symbol)
        """

        try:
            conn.cursor().execute("BEGIN")
            for index, row in df.iterrows():
                curr.execute(merge_query,
                         (row['date'], row['open'], row['high'], row['low'],
                          row['close'], row['volume'], row['symbol']))
            conn.cursor().execute("COMMIT")
            print("Data inserted successfully.")
        except Exception as e:
            conn.cursor().execute("ROLLBACK")
            print(f"Error inserting data: {e}")
        finally:
            curr.close()
            conn.close()


    @task()
    def check_table_stats():
        """Fetch and print the first row to verify data insertion."""
        conn = return_snowflake_conn()
        curr = conn.cursor()
        try:
            curr.execute("SELECT * FROM LAB2_work.raw_data_lab2.stock_prices_symbols LIMIT 1")
            first_row = curr.fetchone()
            print(f"First row in the table: {first_row}")
        except Exception as e:
            print(f"Error fetching data: {e}")
        finally:
            curr.close()
            conn.close()

    # Task dependencies
    symbols = ['AAPL', 'MSFT']  # You can set the symbol dynamically
    stock_data = extract(symbols)
    create_table = create_stock_prices_table()
    insert_data = insert_stock_prices(stock_data)
    check_stats = check_table_stats()

    create_table >> stock_data >> insert_data >> check_stats
