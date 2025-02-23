import pandas as pd
import numpy as np
import yfinance as yf
import ruptures as rpt

# -------------------------
# Pivot Detection Functions
# -------------------------
def checkhl(data_back, data_forward, hl):
    """
    Check if the reference value (last of data_back) is a pivot high or low.
    For a pivot high: ref must be >= every value in data_back (except itself)
    and > every value in data_forward.
    For a pivot low: ref must be <= every value in data_back (except itself)
    and < every value in data_forward.
    """
    ref = data_back[-1]
    if hl == 'high':
        return all(ref >= x for x in data_back[:-1]) and all(ref > x for x in data_forward)
    elif hl == 'low':
        return all(ref <= x for x in data_back[:-1]) and all(ref < x for x in data_forward)
    return False

def pivot(osc, LBL, LBR, highlow):
    """
    Scans an oscillator (pd.Series) and returns a list where pivot points (high or low)
    are marked with their value and non‑pivot points are NaN.
    
    Parameters:
      - osc: pd.Series of the oscillator.
      - LBL: number of bars to the left (including current bar).
      - LBR: number of bars to the right.
      - highlow: 'high' or 'low' specifying which pivot to look for.
    """
    pivots = [np.nan] * len(osc)
    for i in range(LBL, len(osc) - LBR):
        left = osc.iloc[i - LBL:i + 1].values
        right = osc.iloc[i + 1:i + LBR + 1].values
        if checkhl(left, right, highlow):
            pivots[i] = osc.iloc[i]
    return pivots

# -------------------------------
# Change Point Detection Function
# -------------------------------
def detect_change_points(series, model="rbf", pen=10):
    """
    Uses the ruptures package (PELT algorithm) to detect change points in a series.
    
    Parameters:
      - series: pd.Series of the price (or any numeric series).
      - model: model to use (default 'rbf').
      - pen: penalty value for change point detection.
    
    Returns:
      - A list of indices where change points were detected.
    """
    algo = rpt.Pelt(model=model).fit(series.values)
    cp_indices = algo.predict(pen=pen)
    return cp_indices

# -------------------------------
# Generate Combined Signals with "signal" Column
# -------------------------------
def generate_signals(price_data, oscillator, LBL=3, LBR=3, cp_penalty=10, cp_model="rbf", cp_window=5):
    """
    Combines pivot detection and change point detection to generate buy and sell signals.
    Then creates a "signal" column that is 'buy', 'sell', or 'hold' based on the following:
      - 'buy'  if only a buy signal (pivot low near a change point) is present.
      - 'sell' if only a sell signal (pivot high near a change point) is present.
      - 'hold' in all other cases.
    
    Parameters:
      - price_data: pd.Series of prices.
      - oscillator: pd.Series used for pivot detection.
      - LBL, LBR: Number of bars to the left/right for pivot determination.
      - cp_penalty: Penalty parameter for change point detection.
      - cp_model: Model parameter for CPD.
      - cp_window: Number of bars around a detected change point within which a pivot
                   will trigger a signal.
    
    Returns:
      - A DataFrame containing the price, oscillator, pivot highs/lows,
        change point markers, buy/sell booleans, and the combined "signal" column.
    """
    # 1. Calculate pivot highs and lows from the oscillator.
    pvtHigh = pivot(oscillator, LBL, LBR, 'high')
    pvtLow = pivot(oscillator, LBL, LBR, 'low')
    
    # 2. Create a DataFrame for signals.
    signals = pd.DataFrame(index=price_data.index)
    signals['price'] = price_data
    signals['osc'] = oscillator
    signals['pvtHigh'] = pvtHigh
    signals['pvtLow'] = pvtLow

    # 3. Detect change points on the price series.
    cp_indices = detect_change_points(price_data, model=cp_model, pen=cp_penalty)
    signals['change_point'] = 0
    for cp in cp_indices:
        if cp < len(signals):  # cp_indices includes the final index sometimes
            signals.iloc[cp, signals.columns.get_loc('change_point')] = 1

    # 4. Generate buy and sell signals.
    #    - Buy when a pivot low is within ±cp_window of a change point.
    #    - Sell when a pivot high is within ±cp_window of a change point.
    signals['buy_signal'] = False
    signals['sell_signal'] = False
    
    for i in range(len(signals)):
        window_start = max(0, i - cp_window)
        window_end = min(len(signals)-1, i + cp_window)
        if signals['change_point'].iloc[window_start:window_end+1].sum() > 0:
            if not np.isnan(signals['pvtLow'].iloc[i]):
                signals.at[signals.index[i], 'buy_signal'] = True
            if not np.isnan(signals['pvtHigh'].iloc[i]):
                signals.at[signals.index[i], 'sell_signal'] = True

    # 5. Create a "signal" column:
    #    - 'buy' if there is a buy signal only,
    #    - 'sell' if there is a sell signal only,
    #    - 'hold' otherwise (if neither signal or if both signals occur simultaneously).
    def get_signal(row):
        if row['buy_signal'] and not row['sell_signal']:
            return 'buy'
        elif row['sell_signal'] and not row['buy_signal']:
            return 'sell'
        else:
            return 'hold'
        
    signals['signal'] = signals.apply(get_signal, axis=1)
    
    return signals


def get_pvt_signals(data):
    """
    Given a DataFrame 'data' (with a datetime index) that contains a 'Close' column,
    this function calculates pivot signals combined with change point detection.
    
    It then merges the active signals (where a buy or sell signal is triggered)
    back into the original data based on the datetime index, removes the temporary
    'buy_signal' and 'sell_signal' columns, and renames the 'signal' column to 
    'cpd_pvt_signals'.
    
    Parameters:
        data (pd.DataFrame): The input DataFrame with at least a 'Close' column.
        
    Returns:
        pd.DataFrame: The merged DataFrame with the new column 'cpd_pvt_signals'.
    """
    # Use the closing price as both price and oscillator.
    price = data['Close']
    oscillator = price.copy()
    
    # Generate signals using the previously defined function.
    signals = generate_signals(price, oscillator, LBL=5, LBR=5, cp_penalty=20, cp_model="rbf", cp_window=8)
    
    # Filter out only the active signals (rows with either a buy or sell signal).
    active_signals = signals[(signals['buy_signal']) | (signals['sell_signal'])]
    
    # Merge the active signals back into the original data based on datetime index.
    # (Ensure that 'data' has its datetime as the index.)
    merged_data = data.merge(active_signals, left_index=True, right_index=True, how='left')
    
    # Remove the temporary signal flag columns.
    merged_data.drop(columns=['buy_signal', 'sell_signal'], inplace=True, errors='ignore')
    
    # Rename the 'signal' column to 'cpd_pvt_signals' if it exists.
    if 'signal' in merged_data.columns:
        merged_data.rename(columns={'signal': 'cpd_pvt_signals'}, inplace=True)
    
    return merged_data


# def get_pvt_signals(data):
#     print(data)
#     price = data['Close']
#     oscillator = price.copy()
#     signals = generate_signals(price, oscillator, LBL=3, LBR=3, cp_penalty=10, cp_model="rbf", cp_window=5)
#     active_signals = signals[(signals['buy_signal']) | (signals['sell_signal'])]
#     print(active_signals)
#     return active_signals

