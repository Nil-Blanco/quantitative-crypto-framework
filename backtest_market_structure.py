import pandas as pd
from binance.client import Client
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter

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
symbol = "SOLUSDT"  # Configured for your Ethereum 500-day test
interval = Client.KLINE_INTERVAL_1DAY
start_time = "300 days ago UTC" # Period matching your terminal screenshot

initial_capital = 10000.0
exchange_fee = 0.001  # 0.1% Binance spot fee
sl_buffer = 0.995     # 0.5% buffer below the pullback floor

# Fetch market data
df = fetch_historical_data(symbol, interval, start_time)

# 2. TECHNICAL INDICATORS & MARKET STRUCTURE
print("Computing technical indicators and structural pivots...")

df['SMA_20'] = df['Close'].rolling(window=20).mean()
df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

# Define Structural Pivot Low (Pullback Floor)
df['Is_Pivot_Low'] = (
    (df['Low'].shift(2) < df['Low'].shift(4)) &
    (df['Low'].shift(2) < df['Low'].shift(3)) &
    (df['Low'].shift(2) < df['Low'].shift(1)) &
    (df['Low'].shift(2) < df['Low'].shift(0))
)
df['Pivot_Value'] = df['Low'].shift(2)

# --- ENTRY LOGIC ---
was_below = (df['Close'].shift(2) < df['SMA_20'].shift(2)) | (df['Close'].shift(2) < df['EMA_21'].shift(2))
crossed_above = (df['Close'].shift(1) > df['SMA_20'].shift(1)) & (df['Close'].shift(1) > df['EMA_21'].shift(1))
df['Long_Signal'] = was_below & crossed_above

# Pre-calculate Buy & Hold Baseline for the plot
initial_price = df['Close'].iloc[0]
df['Buy_Hold_Equity'] = (initial_capital / initial_price) * df['Close']

# Initialize Bot Equity Curve column
df['Bot_Equity'] = initial_capital

# 3. BACKTEST ENGINE (SCALE-OUT + STRUCTURAL TRAILING)
print("\nInitiating Scale-Out Backtest Engine...")

# Portfolio Tracking
balance_usdt = initial_capital
balance_asset = 0.0

position = "NONE" 
entry_price = 0.0
stop_loss_price = 0.0
take_profit_target = 0.0
scaled_out = False
recent_confirmed_floor = 0.0

total_trades = 0
winning_trades = 0
losing_trades = 0
equity_before_trade = 0.0

# Prepare to store data points for the plot
equity_curve_dates = []
equity_curve_values = []

for i, (date, row) in enumerate(df.iterrows()):
    if pd.isna(row['SMA_20']):
        # For plot warming up, maintain previous equity value
        df.at[date, 'Bot_Equity'] = initial_capital if i == 0 else df['Bot_Equity'].iloc[i-1]
        continue

    # Track the most recent confirmed pullback floor globally
    if row['Is_Pivot_Low']:
        recent_confirmed_floor = row['Pivot_Value']

    # Update dynamic equity if we are IN a trade (current value in USDT)
    if position == "LONG":
        current_equity = balance_usdt + (balance_asset * row['Close'])
        df.at[date, 'Bot_Equity'] = current_equity
    else:
        # Otherwise, maintain previous balance
        df.at[date, 'Bot_Equity'] = df['Bot_Equity'].iloc[i-1] if i > 0 else initial_capital

    # --- STATE: IN CASH ---
    if position == "NONE":
        if row['Long_Signal']:
            if recent_confirmed_floor == 0.0:
                recent_confirmed_floor = row['Low']
                
            entry_price = row['Close']
            position = "LONG"
            equity_before_trade = balance_usdt
            
            # Buy the asset
            balance_asset = (balance_usdt * (1 - exchange_fee)) / entry_price
            balance_usdt = 0.0
            
            # Set Initial Risk Parameters
            stop_loss_price = recent_confirmed_floor * sl_buffer
            initial_risk = entry_price - stop_loss_price
            
            # Set Take Profit at 1:2 Risk/Reward Ratio
            take_profit_target = entry_price + (initial_risk * 2.0)
            scaled_out = False
            
            print(f"[{date.strftime('%Y-%m-%d')}] 🟢 LONG at ${entry_price:.2f} | SL: ${stop_loss_price:.2f} | TP Target: ${take_profit_target:.2f}")

    # --- STATE: ACTIVE LONG ---
    elif position == "LONG":
        
        # 1. CHECK TAKE PROFIT (Intraday High hits the target)
        if False and not scaled_out and row['High'] >= take_profit_target:
            # Sell 50% of the position
            units_to_sell = balance_asset * 0.5
            balance_usdt += units_to_sell * take_profit_target * (1 - exchange_fee)
            balance_asset -= units_to_sell
            scaled_out = True
            
            # Move Stop Loss to Breakeven (Risk-Free Trade)
            if stop_loss_price < entry_price:
                stop_loss_price = entry_price
                
            print(f"[{date.strftime('%Y-%m-%d')}] ⭐ SCALE-OUT: 50% sold at ${take_profit_target:.2f} | SL moved to Breakeven (${stop_loss_price:.2f})")

        # 2. UPDATE STRUCTURAL TRAILING STOP (If new floor confirmed)
        if row['Is_Pivot_Low']:
            potential_new_sl = row['Pivot_Value'] * sl_buffer
            if potential_new_sl > stop_loss_price:
                stop_loss_price = potential_new_sl
                print(f"[{date.strftime('%Y-%m-%d')}] 🔼 SL UPDATED to ${stop_loss_price:.2f} (New Pullback Floor)")

        # 3. CHECK STOP LOSS EXIT (Intraday Low hits the floor)
        if row['Low'] <= stop_loss_price:
            exit_price = stop_loss_price
            
            # Sell remaining asset
            balance_usdt += balance_asset * exit_price * (1 - exchange_fee)
            balance_asset = 0.0
            
            # Evaluate Trade Result
            if balance_usdt > equity_before_trade: 
                winning_trades += 1
                result_str = "PROFIT"
            else: 
                losing_trades += 1
                result_str = "LOSS"
                
            total_trades += 1
            
            # Record final trade close for the plot
            df.at[date, 'Bot_Equity'] = balance_usdt
            
            print(f"[{date.strftime('%Y-%m-%d')}] 🔴 FULL CLOSE at ${exit_price:.2f} [{result_str}] | Equity: ${balance_usdt:.2f}\n")
            
            position = "NONE"

# Ensure dynamic equity update after the loop
if position == "LONG":
    final_equity = balance_usdt + (balance_asset * df['Close'].iloc[-1])
    df.at[df.index[-1], 'Bot_Equity'] = final_equity
else:
    final_equity = df['Bot_Equity'].iloc[-1]

# 4. PERFORMANCE METRICS
total_return_pct = ((final_equity - initial_capital) / initial_capital) * 100
win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

buy_and_hold_capital = df['Buy_Hold_Equity'].iloc[-1]
buy_and_hold_return_pct = ((buy_and_hold_capital - initial_capital) / initial_capital) * 100

# 5. GENERATE PLOT (Visual Block)
print("\nGenerating comparative performance plot...")

# Configure styling
sns.set_theme(style="darkgrid")
plt.figure(figsize=(14, 8))


# Plot Equity Curves with dynamic performance metrics in the legend
plt.plot(df.index, df['Bot_Equity'], label=f'Bot Equity Curve ({total_return_pct:.2f}%)', linewidth=2.5, color='#2ecc71')
plt.plot(df.index, df['Buy_Hold_Equity'], label=f'Baseline: Buy & Hold ({buy_and_hold_return_pct:.2f}%)', linewidth=1.5, color='#e74c3c', linestyle='--')

# Configure chart details
plt.title(f'Comparative Performance: Institutional Bot Strategy vs Buy & Hold ({symbol})\nTimeframe: {interval} | Period: {start_time}', fontsize=16, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Equity (USDT)', fontsize=12)

# Format the date axis
date_form = DateFormatter("%Y-%m-%d")
plt.gca().xaxis.set_major_formatter(date_form)
plt.xticks(rotation=45)

# Add Legend and grid
plt.legend(loc='upper left', fontsize=12)
plt.tight_layout()

# Print formatted report
print("\n" + "="*50)
print("             INSTITUTIONAL BACKTEST REPORT")
print("="*50)
print(f"Strategy      : Breakout + Scale-Out + Structural SL")
print(f"Asset         : {symbol}")
print(f"Timeframe     : {interval}")
print(f"Test Period   : {start_time}")
print("-" * 50)
print(f"Initial Equity: ${initial_capital:.2f}")
print(f"Final Equity  : ${final_equity:.2f} ({total_return_pct:.2f}%)")
print(f"Buy & Hold    : ${buy_and_hold_capital:.2f} ({buy_and_hold_return_pct:.2f}%)")
print("-" * 50)
print(f"Total Trades  : {total_trades}")
print(f"Win Rate      : {win_rate:.2f}%")
print(f"Wins / Losses : {winning_trades} / {losing_trades}")
print("="*50)

# Display the plot window
print("\nDisplaying plot window...")
plt.show()