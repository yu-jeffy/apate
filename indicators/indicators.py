import pandas as pd

def calculate_sma(data, window):
    return data['price'].rolling(window=window).mean()

def calculate_ema(data, window):
    return data['price'].ewm(span=window, adjust=False).mean()

def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    ema_short = calculate_ema(data, short_window)
    ema_long = calculate_ema(data, long_window)
    macd = ema_short - ema_long
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal

def calculate_rsi(data, window=14):
    delta = data['price'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    average_gain = gain.rolling(window=window).mean()
    average_loss = loss.rolling(window=window).mean()
    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(data, window=20, num_std_dev=2):
    sma = calculate_sma(data, window)
    std_dev = data['price'].rolling(window=window).std()
    upper_band = sma + (std_dev * num_std_dev)
    lower_band = sma - (std_dev * num_std_dev)
    return upper_band, lower_band
