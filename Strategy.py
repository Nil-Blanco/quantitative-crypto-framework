import pandas as pd
import numpy as np
import yfinance as yf
import ta
import matplotlib.pyplot as plt

def indicators(df):
    df['SMA_200'] = ta.trend.sma_indicator(df['Close'].squeeze(), window=200)
    df['stoch'] = ta.momentum.stoch(df['High'].squeeze(), df['Low'].squeeze(), df['Close'].squeeze(), window=10)
    df.dropna(inplace=True)

TICKER = 'META' 
df = yf.download(TICKER, start='2016-01-10')

indicators(df)

df['buy'] = (df['Close'].squeeze()>df.SMA_200) & (df.stoch < 5)

df['buyprice'] = np.where(df.buy, df['Close'].squeeze() * 0.97, np.nan)

df.buyprice = df.buyprice.ffill()

df['sellprice'] = df.Open.shift(-1)

for i in range(1, 11):
    df['shifted_low_' + str(i)] = df['Low'].squeeze().shift(-i)
    df['shifted_Close_' + str(i)] = df['Close'].squeeze().shift(-i)

colnames_low = ['shifted_low_' + str(i) for i in range(1, 11)]
colnames_close = ['shifted_Close_' + str(i) for i in range(1, 11)]

raw_signals = df[df.buy]

checkbuys = raw_signals[colnames_low].le(raw_signals.buyprice, axis=0)

checkbuys_sum = checkbuys.cumsum(axis=1) == 1

filter_buys = checkbuys[checkbuys_sum]

raw_trades = filter_buys.T.idxmax()

extract_buys_raw = raw_trades.str[0].str.split('_').str[-1]

extract_buys = extract_buys_raw.fillna(10)

buydates = [df.loc[i:].index[int(e)] for i,e in zip(extract_buys.index,extract_buys.values)]

buy_df = df.loc[buydates]

df_ = pd.DataFrame(extract_buys_raw, columns=['NaN-check'])

df_['buydates'] = buydates

checksells = buy_df[colnames_close].gt(buy_df.buyprice,axis=0)

checksells[colnames_close[-1]] = True

checksells_sum = checksells.cumsum(axis=1) == 1

filter_sells = checksells[checksells_sum]

raw_sells = filter_sells.T.idxmax()

extract_sells = raw_sells.str[0].str.split('_').str[-1].astype(int)

selldates = [df.loc[i:].index[e] for i,e in zip(extract_sells.index,extract_sells.values)]

df_['selldates'] = selldates

df_.loc[df_['NaN-check'].isna(),'selldates'] = df_.loc[df_['NaN-check'].isna()].buydates

trades_ = df_[df_.index > df_.selldates.shift(1)]

real_trades = df_[:1]._append(trades_)

real_trades_executed = real_trades.dropna()

buys = df.loc[real_trades_executed.buydates].buyprice
sells = df.loc[real_trades_executed.selldates].sellprice

profit = (sells.values - buys.values) / buys.values

acc_profit = (profit+1).cumprod()


net_profit_pct = (acc_profit[-1] - 1) * 100

plt.plot(df['Close'], label='Close Price', alpha=0.8)
plt.plot(df['SMA_200'], label='200 SMA', color='orange')
plt.scatter(buys.index, buys.values, marker='^', c='g', s=100, label='Buy')
plt.scatter(sells.index, sells.values, marker='v', c='r', s=100, label='Sell')
plt.title(f"Pullback Strategy Backtest | Net Return: {net_profit_pct:.2f}%", fontsize=14, fontweight='bold')
plt.xlabel("Date", fontsize=12)
plt.ylabel(f"{TICKER} Price ($)", fontsize=12)
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

plt.show()