import pandas as pd
from binance.client import Client

# 1. INITIALIZE API CLIENT
client = Client()

def fetch_historical_data(symbol, interval, start_time):
    print(f"Fetching historical data for {symbol}...")
    klines = client.get_historical_klines(symbol, interval, start_time)
    
    data = []
    for kline in klines:
        timestamp = pd.to_datetime(kline[0], unit='ms')
        data.append({
            'Date': timestamp,
            'Open': float(kline[1]),
            'High': float(kline[2]),
            'Low': float(kline[3]),
            'Close': float(kline[4]),
            'Volume': float(kline[5])
        })
        
    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    return df

# --- HYPERPARAMETERS ---
symbol = "BTCUSDT"
interval = Client.KLINE_INTERVAL_1DAY
start_time = "1000 days ago UTC"

initial_capital = 10000.0
exchange_fee = 0.001  # 0.1% Binance spot fee

# Fetch market data
df = fetch_historical_data(symbol, interval, start_time)

# 2. TECHNICAL INDICATORS & CONFIRMATION LOGIC
print("Computing technical indicators and Confirmation Logic...")

# Moving Averages & Volume
df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()

# --- LONG LOGIC: Cross, Close & Confirmation ---
# 1. Pre-condition (t-2): Price was below at least one of the bands
was_below = (df['Close'].shift(2) < df['SMA_20'].shift(2)) | (df['Close'].shift(2) < df['EMA_21'].shift(2))
# 2. Cross & Close (t-1): Price closed strictly above both bands
crossed_above = (df['Close'].shift(1) > df['SMA_20'].shift(1)) & (df['Close'].shift(1) > df['EMA_21'].shift(1))
# 3. Confirmation (t): Current price closes higher than the breakout candle AND volume validates
confirmation_long = (df['Close'] > df['Close'].shift(1)) & (df['Close'] > df['SMA_20']) & (df['Volume'] > df['Volume_MA_20'])

df['Long_Signal'] = was_below & crossed_above & confirmation_long

# --- SHORT LOGIC: Cross, Close & Confirmation ---
# 1. Pre-condition (t-2): Price was above at least one of the bands
was_above = (df['Close'].shift(2) > df['SMA_20'].shift(2)) | (df['Close'].shift(2) > df['EMA_21'].shift(2))
# 2. Cross & Close (t-1): Price closed strictly below both bands
crossed_below = (df['Close'].shift(1) < df['SMA_20'].shift(1)) & (df['Close'].shift(1) < df['EMA_21'].shift(1))
# 3. Confirmation (t): Current price closes lower than the breakout candle AND volume validates
confirmation_short = (df['Close'] < df['Close'].shift(1)) & (df['Close'] < df['SMA_20']) & (df['Volume'] > df['Volume_MA_20'])

df['Short_Signal'] = was_above & crossed_below & confirmation_short

# 3. BACKTEST ENGINE (STOP & REVERSE)
print("\nInitiating backtest engine...")

capital = initial_capital
position = "NONE" 
entry_price = 0.0

total_trades = 0
winning_trades = 0
losing_trades = 0

for date, row in df.iterrows():
    if pd.isna(row['SMA_20']):
        continue

    # --- STATE: NO ACTIVE POSITION ---
    if position == "NONE":
        if row['Long_Signal']:
            entry_price = row['Close']
            position = "LONG"
            capital *= (1 - exchange_fee)
            print(f"[{date.strftime('%Y-%m-%d')}] EXECUTE LONG at ${entry_price:.2f}")
            
        elif row['Short_Signal']:
            entry_price = row['Close']
            position = "SHORT"
            capital *= (1 - exchange_fee)
            print(f"[{date.strftime('%Y-%m-%d')}] EXECUTE SHORT at ${entry_price:.2f}")

    # --- STATE: ACTIVE LONG ---
    elif position == "LONG":
        # Check for Short Signal to reverse position
        if row['Short_Signal']:
            exit_price = row['Close']
            
            # Close Long
            trade_return = exit_price / entry_price
            capital = capital * trade_return * (1 - exchange_fee)
            
            if exit_price > entry_price: 
                winning_trades += 1
            else: 
                losing_trades += 1
            total_trades += 1
            
            print(f"[{date.strftime('%Y-%m-%d')}] CLOSE LONG & REVERSE TO SHORT at ${exit_price:.2f} | Equity: ${capital:.2f}")
            
            # Open Short
            entry_price = exit_price
            position = "SHORT"
            capital *= (1 - exchange_fee)

    # --- STATE: ACTIVE SHORT ---
    elif position == "SHORT":
        # Check for Long Signal to reverse position
        if row['Long_Signal']:
            exit_price = row['Close']
            
            # Close Short
            trade_return = 1 + ((entry_price - exit_price) / entry_price)
            capital = capital * trade_return * (1 - exchange_fee)
            
            if exit_price < entry_price: 
                winning_trades += 1
            else: 
                losing_trades += 1
            total_trades += 1
            
            print(f"[{date.strftime('%Y-%m-%d')}] CLOSE SHORT & REVERSE TO LONG at ${exit_price:.2f} | Equity: ${capital:.2f}")
            
            # Open Long
            entry_price = exit_price
            position = "LONG"
            capital *= (1 - exchange_fee)

# 4. PERFORMANCE METRICS
total_return_pct = ((capital - initial_capital) / initial_capital) * 100
win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

# Buy & Hold calculation for baseline comparison
initial_price = df['Close'].iloc[0]
final_price = df['Close'].iloc[-1]
buy_and_hold_capital = (initial_capital / initial_price) * final_price
buy_and_hold_return_pct = ((buy_and_hold_capital - initial_capital) / initial_capital) * 100

# Print formatted report
print("\n" + "="*45)
print("             BACKTEST REPORT")
print("="*45)
print(f"Strategy      : BMSB Breakout & Confirmation")
print(f"Asset         : {symbol}")
print(f"Timeframe     : {interval}")
print("-" * 45)
print(f"Initial Equity: ${initial_capital:.2f}")
print(f"Final Equity  : ${capital:.2f} ({total_return_pct:.2f}%)")
print(f"Buy & Hold    : ${buy_and_hold_capital:.2f} ({buy_and_hold_return_pct:.2f}%)")
print("-" * 45)
print(f"Total Trades  : {total_trades}")
print(f"Win Rate      : {win_rate:.2f}%")
print(f"Wins / Losses : {winning_trades} / {losing_trades}")
print("="*45)