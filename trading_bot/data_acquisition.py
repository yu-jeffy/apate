import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_unix_timestamp(dt):
    return int(time.mktime(dt.timetuple()))

def get_historical_data(start_date, end_date, vs_currency='usd'):
    """
    Fetch historical BTC price data between specified dates.
    """
    id = 'bitcoin'
    url = f'https://api.coingecko.com/api/v3/coins/{id}/market_chart/range'

    from_timestamp = get_unix_timestamp(start_date)
    to_timestamp = get_unix_timestamp(end_date)

    params = {
        'vs_currency': vs_currency,
        'from': from_timestamp,
        'to': to_timestamp
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

def save_market_data(data, filename='market_data.json'):
    filepath = os.path.join(DATA_DIR, filename)
    data.to_json(filepath, orient='records', date_format='iso')

def load_market_data(filename='market_data.json'):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        return pd.read_json(filepath, convert_dates=['timestamp'])
    else:
        print(f"No market data found at {filepath}")
        return None

_cached_price = None
_cache_expiry = 0

def get_current_price(vs_currency='usd', retries=3, delay=5, cache_duration=60):
    """
    Fetch the current BTC price with error handling and caching.
    """
    global _cached_price, _cache_expiry
    current_time = time.time()
    
    # Return cached price if valid
    if _cached_price is not None and current_time < _cache_expiry:
        return _cached_price
    
    id = 'bitcoin'
    url = f'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': id,
        'vs_currencies': vs_currency
    }
    attempt = 0
    while attempt < retries:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            price = data[id][vs_currency]
            _cached_price = price
            _cache_expiry = current_time + cache_duration
            return price
        elif response.status_code == 429:
            print(f"Rate limit exceeded. Retrying in {delay} seconds...")
            time.sleep(delay)
            attempt += 1
        else:
            print(f"Error fetching current price: {response.status_code}")
            return None
    print("Failed to fetch current price after retries.")
    return None
