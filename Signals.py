import streamlit as st

st.set_page_config(
    page_title="Radon Research",
    layout="wide"
)

import pandas as pd
import yfinance as yf
import os 
from pathlib import Path
import traceback as tr
from datetime import datetime
from pvtlevels_signals import get_pvt_signals

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

def get_data(stock):
    # File path in stocks_data folder
    file_path = Path(f"stocks_data/{stock}.csv")
    
    # Check if file exists and is created today
    if file_path.exists():
        created_date = datetime.fromtimestamp(file_path.stat().st_ctime).date()
        today = datetime.now().date()
        if created_date == today:
            print(f"Reading today's data from {file_path}")
            return pd.read_csv(file_path)
    
    # If file doesn't exist or is not today's, fetch data from yfinance
    print("Fetching data from yfinance...")
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
    # Buy/Sell Conditions
    conditions = [
        (data['MACD'] > 1) & (data['MACD'] > data['Signal']) & (data['MACD_Hist'] > 1) & (data['RSI'] > 40),
        (data['MACD'] < -1) & (data['MACD'] < data['Signal']) & (data['MACD_Hist'] < -1) & (data['RSI'] < 60)
    ]
    data['macd_signals'] = None
    data.loc[conditions[0], 'macd_signals'] = 'Buy'
    data.loc[conditions[1], 'macd_signals'] = 'Sell'

    # Save to CSV
    # os.makedirs("stocks_data", exist_ok=True)
    # data.to_csv(file_path, index=False)
    data = get_pvt_signals(data)
    return data

def start_bot():
    nifty_stocks = pd.read_csv('imp_files/nifty_100.csv')
    nifty_stocks.columns = [col.split()[0] for col in nifty_stocks.columns]
    stocks = nifty_stocks['SYMBOL'].tolist()
    # stocks = ["M&M"]
    signal_data = []
    for stock in stocks:
        try:
            data = get_data(stock)
            signal_data.append(data)
        except Exception as e:
            print(f"Error fetching data for {stock}: {e}")

    return pd.concat(signal_data)

temp_output = start_bot()

temp_output = temp_output.reset_index()
output = temp_output[temp_output['Datetime'] > '2025-02-04']

output.to_csv("output.csv",index=False)

# Combine buy and sell signals into one DataFrame with a 'final_signal' column
output['final_signal'] = None
output.loc[(output['cpd_pvt_signals'] == 'buy') & (output['macd_signals'] == 'Buy'), 'final_signal'] = 'Buy'
output.loc[(output['cpd_pvt_signals'] == 'sell') & (output['macd_signals'] == 'Sell'), 'final_signal'] = 'Sell'

# Filter only rows with final signals and sort by date
final_signals = output[output['final_signal'].notna()].sort_values(by='Datetime', ascending=False)
final_signals = final_signals[['Datetime', 'Stock', 'Close', "RSI",'final_signal']]
final_signals['Datetime'] = pd.to_datetime(final_signals['Datetime']).dt.strftime('%d-%b-%y %H:%M')


# Display the most recent 10 signals
st.write("Recent Signals (Last 10)")
st.write(f"Total Signals: {len(final_signals)} | Buy Signals: {len(final_signals[final_signals['final_signal']=="Buy"])} | Sell Signals: {len(final_signals[final_signals['final_signal']=="Sell"])}", )

# st.write(final_signals.head(10).reset_index(drop=True))
st.dataframe(final_signals.head(10).reset_index(drop=True), use_container_width=True)  # Full width and custom height