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

# Risk Management Parameters
initial_sl_pct = 0.07    # 7% hard stop loss initially
trailing_sl_pct = 0.15   # 15% dynamic trailing stop behind the highest peak

# Fetch market data
df = fetch_historical_data(symbol, interval, start_time)

# 2. TECHNICAL INDICATORS & CONFIRMATION LOGIC
print("Computing technical indicators and Confirmation Logic...")

df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
df['Volume_MA_20'] = df['Volume'].rolling(window=20).mean()

# --- ENTRY LOGIC: Cross, Close & Confirmation ---
was_below = (df['Close'].shift(2) < df['SMA_20'].shift(2)) | (df['Close'].shift(2) < df['EMA_21'].shift(2))
crossed_above = (df['Close'].shift(1) > df['SMA_20'].shift(1)) & (df['Close'].shift(1) > df['EMA_21'].shift(1))
confirmation_long = (df['Close'] > df['Close'].shift(1)) & (df['Close'] > df['SMA_20']) & (df['Volume'] > df['Volume_MA_20'])

df['Long_Signal'] = was_below & crossed_above & confirmation_long

# --- EXIT TREND LOGIC (Optional safety net if market turns slow) ---
df['Trend_Broken'] = (df['Close'] < df['SMA_20']) & (df['Close'] < df['EMA_21'])

# 3. BACKTEST ENGINE (LONG ONLY + TRAILING STOP)
print("\nInitiating Long-Only backtest engine...")

capital = initial_capital
position = "NONE" 
entry_price = 0.0
stop_loss_price = 0.0
highest_peak = 0.0

total_trades = 0
winning_trades = 0
losing_trades = 0

for date, row in df.iterrows():
    if pd.isna(row['SMA_20']):
        continue

    # --- STATE: NO ACTIVE POSITION (IN CASH) ---
    if position == "NONE":
        if row['Long_Signal']:
            entry_price = row['Close']
            position = "LONG"
            capital *= (1 - exchange_fee)
            
            # Initialize risk variables
            highest_peak = entry_price
            stop_loss_price = entry_price * (1 - initial_sl_pct)
            
            print(f"[{date.strftime('%Y-%m-%d')}] 🟢 EXECUTE LONG at ${entry_price:.2f} | Initial SL: ${stop_loss_price:.2f}")

    # --- STATE: ACTIVE LONG ---
    elif position == "LONG":
        # 1. Update the Trailing Stop if price makes a new high
        if row['High'] > highest_peak:
            highest_peak = row['High']
            potential_new_sl = highest_peak * (1 - trailing_sl_pct)
            
            # The Stop Loss can only go UP, never down.
            if potential_new_sl > stop_loss_price:
                stop_loss_price = potential_new_sl

        # 2. Check Exits (Did we hit the Stop Loss today?)
        # We check against 'Low' because intra-day volatility might trigger it
        if row['Low'] <= stop_loss_price:
            exit_price = stop_loss_price # Assumes market execution at SL
            trade_return = exit_price / entry_price
            capital = capital * trade_return * (1 - exchange_fee)
            
            if exit_price > entry_price: 
                winning_trades += 1
                result_str = "PROFIT (Trailing Stop)"
            else: 
                losing_trades += 1
                result_str = "LOSS (Stop Loss)"
                
            total_trades += 1
            print(f"[{date.strftime('%Y-%m-%d')}] 🔴 CLOSE LONG at ${exit_price:.2f} [{result_str}] | Equity: ${capital:.2f}")
            
            # Reset to Cash
            position = "NONE"
            
        # 3. Check Alternative Exit (Trend completely broken before hitting SL)
        elif row['Trend_Broken']:
            exit_price = row['Close']
            trade_return = exit_price / entry_price
            capital = capital * trade_return * (1 - exchange_fee)
            
            if exit_price > entry_price: 
                winning_trades += 1
                result_str = "PROFIT (Trend Death)"
            else: 
                losing_trades += 1
                result_str = "LOSS (Trend Death)"
                
            total_trades += 1
            print(f"[{date.strftime('%Y-%m-%d')}] 🔴 CLOSE LONG at ${exit_price:.2f} [{result_str}] | Equity: ${capital:.2f}")
            
            position = "NONE"

# 4. PERFORMANCE METRICS
total_return_pct = ((capital - initial_capital) / initial_capital) * 100
win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

initial_price = df['Close'].iloc[0]
final_price = df['Close'].iloc[-1]
buy_and_hold_capital = (initial_capital / initial_price) * final_price
buy_and_hold_return_pct = ((buy_and_hold_capital - initial_capital) / initial_capital) * 100

print("\n" + "="*45)
print("             BACKTEST REPORT")
print("="*45)
print(f"Strategy      : Long-Only + Dynamic Trailing SL")
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