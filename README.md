# Radon Research

## Overview
`signals.py` is a Python-based bot that uses technical indicators like RSI, MACD, and custom pivot levels to generate buy and sell signals for Nifty 100 stocks. The app is built using Streamlit for its UI, integrates with Yahoo Finance to fetch stock data, and processes signals using custom logic.

---

## Features

- **RSI Calculation:** Implements Relative Strength Index (RSI) to measure stock momentum.
- **MACD Analysis:** Uses MACD (Moving Average Convergence Divergence) and Signal Line to identify trends.
- **Custom Pivot Signals:** Incorporates custom logic for pivot-based signals via `pvtlevels_signals`.
- **Live Data Fetching:** Fetches up-to-date stock data from Yahoo Finance.
- **Signal Filtering:** Combines multiple indicators to output strong buy/sell signals.
- **Streamlit Integration:** Displays results in a responsive web UI.

---

## Installation

1. Clone this repository:
    ```bash
    git clone https://github.com/your-repo/signals-bot.git
    cd signals-bot
    ```
2. Create a virtual environment and activate it:
    ```bash
    python -m venv env
    source env/bin/activate  # Linux/macOS
    env\Scripts\activate  # Windows
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Ensure `imp_files/nifty_100.csv` exists with a list of Nifty 100 stock symbols.

---

## Usage

1. Run the application:
    ```bash
    streamlit run signals.py
    ```
2. Open your browser at `http://localhost:8501` to view the app.

---

## File Details

### `signals.py`
- **Functions:**
  - `rsi(ohlc, period)`: Calculates RSI for a given stock's OHLC data.
  - `get_data(stock)`: Fetches stock data, computes indicators, and saves processed data.
  - `start_bot()`: Fetches and processes data for all stocks listed in `nifty_100.csv`.
- **Output:**
  - Displays recent buy/sell signals in the Streamlit app.
  - Saves full output to `output.csv`.

### Supporting Files
- **`pvtlevels_signals.py`**: Custom pivot level signal generation.
- **`stocks_data/`**: Stores cached stock data in CSV format.
- **`imp_files/nifty_100.csv`**: Contains a list of Nifty 100 stock symbols.

---

## Indicators Used

### Relative Strength Index (RSI)
- **Buy Signal:** RSI < 30
- **Sell Signal:** RSI > 65

### Moving Average Convergence Divergence (MACD)
- **Buy Signal:** MACD > Signal Line and MACD Histogram > 1
- **Sell Signal:** MACD < Signal Line and MACD Histogram < -1

### Pivot Level Signals
- Custom buy/sell logic based on pivot points.

---

## Output

### Signal Format
- **Datetime:** Timestamp of the signal
- **Stock:** Stock symbol
- **Close:** Last closing price
- **RSI:** RSI value
- **Final Signal:** 'Buy' or 'Sell'

### Example
| Datetime       | Stock  | Close | RSI  | Final Signal |
|----------------|--------|-------|------|--------------|
| 23-Feb-25 15:15 | TCS    | 3450  | 28.5 | Buy          |
| 23-Feb-25 15:00 | INFY   | 1295  | 72.3 | Sell         |

---

## Future Enhancements

- Add support for additional indicators like Bollinger Bands.
- Integrate with a database for efficient signal storage.
- Real-time notifications for signals.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contributing
Contributions are welcome! Feel free to raise an issue or submit a pull request.
