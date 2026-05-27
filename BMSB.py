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

# 2. TECHNICAL INDICATORS
print("Computing technical indicators (BMSB & Volume)...")

# 20-period Simple Moving Average
df['SMA_20'] = df['Close'].rolling(window=20).mean()

# 21-period Exponential Moving Average
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

# 20-period Volume Moving Average
df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()

# Logic Signals
df['Long_Signal'] = (df['Close'] > df['SMA_20']) & (df['Close'] > df['EMA_21']) & (df['Volume'] > df['Volume_MA_20'])
df['Short_Signal'] = (df['Close'] < df['SMA_20']) & (df['Close'] < df['EMA_21']) & (df['Volume'] > df['Volume_MA_20'])

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
            print(f"[{date}] EXECUTE LONG at ${entry_price:.2f}")
            
        elif row['Short_Signal']:
            entry_price = row['Close']
            position = "SHORT"
            capital *= (1 - exchange_fee)
            print(f"[{date}] EXECUTE SHORT at ${entry_price:.2f}")

    # --- STATE: ACTIVE LONG ---
    elif position == "LONG":
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
            
            print(f"[{date}] CLOSE LONG & REVERSE TO SHORT at ${exit_price:.2f} | Equity: ${capital:.2f}")
            
            # Open Short
            entry_price = exit_price
            position = "SHORT"
            capital *= (1 - exchange_fee)

    # --- STATE: ACTIVE SHORT ---
    elif position == "SHORT":
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
            
            print(f"[{date}] CLOSE SHORT & REVERSE TO LONG at ${exit_price:.2f} | Equity: ${capital:.2f}")
            
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
print(f"Strategy      : Bull Market Support Band Breakout")
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