import os
import sqlite3
import ccxt
import pandas as pd
from datetime import datetime

# Path setup
DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, 'trading_bot.db')

def init_db():
    """Initializes the local SQLite database and creates the price table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table for 1-hour OHLCV candlestick data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS btc_hourly_prices (
            timestamp TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("✓ Local database initialized successfully.")

def fetch_and_store_btc_data(days_back=30):
    """Fetches historical BTC/USDT hourly data from Binance (No API key needed) 
    and saves/updates it in the local SQLite DB."""
    
    # Instantiate the exchange (Binance public endpoints)
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    
    symbol = 'BTC/USDT'
    timeframe = '1h'  # 1-hour intervals
    
    # Calculate milliseconds timestamp for historical query start
    since = exchange.milliseconds() - days_back * 24 * 60 * 60 * 1000
    
    print(f"Fetching historical data for {symbol} starting from {days_back} days ago...")
    
    try:
        # Fetch data via CCXT unified API
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)
        
        # Convert to Pandas DataFrame for easier manipulation
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Format timestamp from ms to human-readable strings (ISO standard string format)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Connect and write data to SQLite
        conn = sqlite3.connect(DB_PATH)
        
        # 'replace' ensures we overwrite overlaps and avoid unique constraint errors
        df.to_sql('btc_hourly_prices', conn, if_exists='append', index=False)
        
        # Deduplicate identical rows just in case of overlaps
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM btc_hourly_prices 
            WHERE rowid NOT IN (
                SELECT MIN(rowid) FROM btc_hourly_prices GROUP BY timestamp
            )
        ''')
        
        conn.commit()
        total_rows = cursor.execute("SELECT COUNT(*) FROM btc_hourly_prices").fetchone()[0]
        conn.close()
        
        print(f"✓ Successfully sync'd {len(df)} price intervals. Total rows stored: {total_rows}")
        
    except Exception as e:
        print(f"✕ Error fetching data: {e}")

if __name__ == "__main__":
    init_db()
    # Fetch past 60 days of hourly data to seed our technical analysis indicators
    fetch_and_store_btc_data(days_back=60)
