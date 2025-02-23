import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

def get_data(stock):
    # File path in stocks_data folder
    ticker = yf.Ticker(stock + ".NS")
    data = ticker.history(period='1mo', interval='15m').dropna().reset_index()
    
    # Process data
    try:
        data['Date'] = pd.to_datetime(data['Date'])
    except:
        data['Date'] = pd.to_datetime(data['Datetime'])

    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['Signal']
    data['RSI'] = rsi(data)
    data['rsi_signal'] = data['RSI'].apply(lambda x: 'Buy' if x < 30 else ('Sell' if x > 65 else 'Hold'))
    data['Stock'] = stock
    return data.tail(1)[['Date','Stock', 'Close', 'MACD', 'Signal', 'MACD_Hist', 'RSI']]


def rsi(ohlc: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI) using Exponential Moving Averages.
    """
    delta = ohlc["Close"].diff()

    # Separate gains and losses
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0  # Keep only positive changes
    down[down > 0] = 0  # Keep only negative changes

    # Calculate the Exponentially Weighted Moving Average (EMA) for gains and losses
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()

    # Calculate Relative Strength (RS) and RSI
    RS = _gain / _loss
    rsi_series = 100 - (100 / (1 + RS))

    return pd.Series(rsi_series, name="RSI")

file_path = os.path.join(current_dir, "../imp_files/nifty_100.csv")

nifty_stocks = pd.read_csv(file_path)  
nifty_stocks.columns = [col.split()[0] for col in nifty_stocks.columns]
stocks = nifty_stocks['SYMBOL'].tolist()
indicator_data = []
for stock in stocks:
    try:
        data = get_data(stock)
        indicator_data.append(data)
    except Exception as e:
        print(f"Error fetching data for {stock}: {e}")


# Concatenate the DataFrames
full_data = pd.concat(indicator_data, ignore_index=True)
full_data['Date'] = pd.to_datetime(full_data['Date']).dt.strftime('%d-%b-%y %H:%M')

# Set Streamlit layout options
st.set_page_config(layout="wide")  # Full-width layout

# Display the DataFrame
st.dataframe(full_data, use_container_width=True, height=800)  # Full width and custom height