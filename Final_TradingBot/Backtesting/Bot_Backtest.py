from typing import Counter
import pandas as pd
import numpy as np
import config_real
import csv
from binance.client import Client
import talib

#######################################################################################
TRADE_SYMBOL = "DOGEBUSD"
#######################################################################################

client = Client(config_real.API_KEY, config_real.API_SECRET)

csvfile = open('data_Backtesting.csv', 'w', newline='')
candlestick_writer = csv.writer(csvfile, delimiter=',')


candlesticks = client.get_historical_klines(

     "{}".format(TRADE_SYMBOL), Client.KLINE_INTERVAL_1DAY, "1 Jan, 2021", "30 Nov, 2021")

for candlestick in candlesticks:
    candlestick[0] = candlestick[0] / 1000
    toCSV = [candlestick[0], candlestick[1], candlestick[2],
             candlestick[3], candlestick[4], candlestick[5]]
    candlestick_writer.writerow(toCSV)

csvfile.close()
df = pd.read_csv('data_Backtesting.csv', header=None)
df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']
df['time'] = pd.to_datetime(df['time'], unit='s')

#RSI----------------------------------------------------------------------------------------------------------------------------------------------------------
OVERSOLD = 70
OVERBOUGHT = 30
n = 14


def rma(x, n, y0):
    a = (n-1) / n
    ak = a**np.arange(len(x)-1, -1, -1)
    return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]


df['change'] = df['close'].diff()
df['gain'] = df.change.mask(df.change < 0, 0.0)
df['loss'] = -df.change.mask(df.change > 0, -0.0)
df['avg_gain'] = rma(df.gain[n+1:].to_numpy(), n,
                     np.nansum(df.gain.to_numpy()[:n+1])/n)
df['avg_loss'] = rma(df.loss[n+1:].to_numpy(), n,
                     np.nansum(df.loss.to_numpy()[:n+1])/n)
df['rs'] = df.avg_gain / df.avg_loss
df['rsi_14'] = 100 - (100 / (1 + df.rs))

conditions = [
    (df['rsi_14'] > OVERSOLD),
    (df['rsi_14'] < OVERBOUGHT),
    (df['rsi_14'] >= OVERBOUGHT) & (df['rsi_14'] <= OVERSOLD)
]

choices = ['SELL', 'BUY', 'HOLD']

df['decision_RSI'] = np.select(conditions, choices, default="NaN")
df['decision_RSI'].to_numpy()
df['rsi_14'].to_numpy()

#EMA----------------------------------------------------------------------------------------------------------------------------------------------------------
close = df['close'].to_numpy()

df['EMA_short'] = talib.EMA(close, timeperiod=25)
df['EMA_long'] = talib.EMA(close, timeperiod=50)


conditions = [
    (df['EMA_short'] < df['EMA_long']),
    (df['EMA_short'] > df['EMA_long']),
]

choices = ['SELL', 'BUY']

df['decision_EMA'] = np.select(conditions, choices, default='NaN')

#VWAP----------------------------------------------------------------------------------------------------------------------------------------------------------

df['TP'] = (df['high'] + df['low'] + df['close']) / 3
df['timeFrameTotal'] = df['TP'] * df['volume']
df['VWAP'] = df['timeFrameTotal'].cumsum() / df['volume'].cumsum()

VWAP = df['VWAP']
TP = df['TP']

conditions = [
    (df['VWAP'] < TP),
    (df['VWAP'] > TP),
    (df['VWAP'] == TP)]

choices = ['SELL', 'BUY', 'HOLD']

df['decision_VWAP'] = np.select(conditions, choices, default='NaN')

#Trading----------------------------------------------------------------------------------------------------------------------------------------------------------

conditions = [
    (df['decision_VWAP'] == 'SELL') & (df['decision_RSI'] == 'SELL') & (df['decision_EMA'] == 'SELL'),
    (df['decision_VWAP'] == 'SELL') & (df['decision_RSI'] != 'SELL') & (df['decision_EMA'] == 'SELL'),
    (df['decision_VWAP'] == 'SELL') & (df['decision_RSI'] == 'SELL') & (df['decision_EMA'] != 'SELL'),
    (df['decision_VWAP'] != 'SELL') & (df['decision_RSI'] == 'SELL') & (df['decision_EMA'] == 'SELL'),


    (df['decision_VWAP'] == 'BUY') & (df['decision_RSI'] == 'BUY') & (df['decision_EMA'] == 'BUY'),
    (df['decision_VWAP'] == 'BUY') & (df['decision_RSI'] != 'BUY') & (df['decision_EMA'] == 'BUY'),
    (df['decision_VWAP'] == 'BUY') & (df['decision_RSI'] == 'BUY') & (df['decision_EMA'] != 'BUY'),
    (df['decision_VWAP'] != 'BUY') & (df['decision_RSI'] == 'BUY') & (df['decision_EMA'] == 'BUY'),
  
]

choices = ['SELL','SELL','SELL','SELL','BUY','BUY','BUY','BUY',]

df['Final_Decision'] = np.select(conditions, choices, default='HOLD')

initialInv = 50000
capital = initialInv
numbrBTC = 0
binanceFees = 0
fees = 0.001

actualDecision = ""
for i, row in df.iterrows():
    val = row['Final_Decision']
    if val == 'BUY' and numbrBTC == 0:
        numbrBTC = (capital / df.at[i, 'close'])
        binanceFees += (capital * fees)
        capital = 0
        print(df.at[i, 'Final_Decision'], "for Price:", df.at[i, 'close'],
              "get:", "Crypto", numbrBTC, "New Capital:", capital)
        i + 1
    elif (val == 'SELL') and capital == 0:
        capital = (numbrBTC * df.at[i, 'close'])
        binanceFees += (capital * fees)
        numbrBTC = 0
        print(df.at[i, 'Final_Decision'], "for Price:", df.at[i, 'close'],
              "get:", "Crypto", numbrBTC, "New Capital:", capital)
        actualDecision = df.at[i, 'Final_Decision']
        i + 1

#Buy and Hold
buyAndHold = (initialInv / df.iloc[0]['close']) * df['close'][df.index[-1]]


if capital == 0:
    capital = numbrBTC * df['close'][df.index[-1]]



#Display----------------------------------------------------------------------------------------------------------------------------------------------------------

#pd.set_option('display.max_rows', None)
print(df[['time','close','decision_RSI','decision_EMA', 'decision_VWAP', 'Final_Decision']])

print("Initial Investment: ", initialInv)
print("New Capital:", capital)
print("New Assets: ", numbrBTC)
print("Win in %:", ((capital - initialInv) / initialInv) * 100, "%")
print("Trading Fees:", binanceFees)
print("Win incl. Fees:", capital - initialInv - binanceFees)
print("Buy and Hold Capital:", buyAndHold)
print("Difference in WIN between TAIs and BaH:",
      (capital-initialInv - binanceFees) - (buyAndHold - initialInv))



