import alpaca_trade_api as tradeapi
from datetime import datetime
import pytz
import os

# === Alpaca API Setup ===
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = 'https://paper-api.alpaca.markets'

api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

symbol = 'VOO'

# === Get Current Date/Time ===
nyc = pytz.timezone('America/New_York')
now = datetime.now(nyc)
today = now.date()

# === Check if Today is a Trading Day ===
calendar_today = api.get_calendar(start=today.isoformat(), end=today.isoformat())
if not calendar_today:
    print("Market is closed today (holiday or weekend). No action taken.")
    exit()

# === Find Yesterday's Market Day ===
calendar = api.get_calendar(end=today.isoformat(), limit=2)
if len(calendar) < 2:
    print("Not enough historical data (need at least 2 trading days).")
    exit()

yesterday_date = calendar[-2].date
today_date = calendar[-1].date

# === Get Yesterday's Close Price ===
bars_yesterday = api.get_bars(symbol, '1Day', start=yesterday_date.isoformat(), end=yesterday_date.isoformat())
if not bars_yesterday:
    print("No data for yesterday's close.")
    exit()

yesterday_close = bars_yesterday[0].close
print(f"Yesterday's close for {symbol}: ${yesterday_close:.2f}")

# === Get Today's Price Near 3:59 PM ===
bars_today = api.get_bars(symbol, '1Min', start=today_date.isoformat(), end=now.isoformat())
if not bars_today:
    print("No trading data for today.")
    exit()

latest_bar = bars_today[-1]
current_price = latest_bar.close
print(f"Current price for {symbol} at {latest_bar.t} is: ${current_price:.2f}")

# === Calculate Percent Change ===
percent_change = (current_price - yesterday_close) / yesterday_close * 100
print(f"{symbol} percent change from yesterday's close: {percent_change:.2f}%")

# === Trading Logic ===
if percent_change < 0:
    amount_to_buy_percent = abs(percent_change) * 10
    qty_to_buy = 1.0 * (amount_to_buy_percent / 100)

    if qty_to_buy > 0:
        print(f"Placing fractional order to buy {qty_to_buy:.4f} shares of {symbol}.")
        api.submit_order(
            symbol=symbol,
            qty=round(qty_to_buy, 4),
            side='buy',
            type='market',
            time_in_force='day'
        )
    else:
        print("Calculated quantity is 0; no action taken.")
else:
    print(f"{symbol} did not drop today; no action taken.")
