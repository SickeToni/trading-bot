import talib
import numpy as np
import pandas as pd


def rma(x, n, y0):
    a = (n-1) / n
    ak = a**np.arange(len(x)-1, -1, -1)
    return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a**np.arange(1, len(x)+1)]


def getRSI(historyDataFrame):

    OVERSOLD = 70
    OVERBOUGHT = 30
    n = 14

    historyDataFrame['change'] = historyDataFrame['close'].diff()
    historyDataFrame['gain'] = historyDataFrame.change.mask(
        historyDataFrame.change < 0, 0.0)
    historyDataFrame['loss'] = - \
        historyDataFrame.change.mask(historyDataFrame.change > 0, -0.0)
    historyDataFrame['avg_gain'] = rma(historyDataFrame.gain[n+1:].to_numpy(), n,
                                       np.nansum(historyDataFrame.gain.to_numpy()[:n+1])/n)
    historyDataFrame['avg_loss'] = rma(historyDataFrame.loss[n+1:].to_numpy(), n,
                                       np.nansum(historyDataFrame.loss.to_numpy()[:n+1])/n)
    historyDataFrame['rs'] = historyDataFrame.avg_gain / \
        historyDataFrame.avg_loss
    historyDataFrame['rsi_14'] = 100 - (100 / (1 + historyDataFrame.rs))

    conditions = [
        (historyDataFrame['rsi_14'] > OVERSOLD),
        (historyDataFrame['rsi_14'] < OVERBOUGHT),
        (historyDataFrame['rsi_14'] >= OVERBOUGHT) & (
            historyDataFrame['rsi_14'] <= OVERSOLD)
    ]

    choices = ['SELL', 'BUY', 'HOLD']
    historyDataFrame['decision_RSI'] = np.select(
        conditions, choices, default="NaN")
    decision = historyDataFrame.iloc[-1, -1]
  
    return decision


def getEMA(historyDataFrame):
    close = historyDataFrame['close'].to_numpy()
    historyDataFrame['EMA_short'] = talib.EMA(close, timeperiod=50)
    historyDataFrame['EMA_long'] = talib.EMA(close, timeperiod=100)
    conditions = [
        (historyDataFrame['EMA_short'] < historyDataFrame['EMA_long']),
        (historyDataFrame['EMA_short'] > historyDataFrame['EMA_long']),
    ]
    choices = ['SELL', 'BUY']
    historyDataFrame['decision_EMA'] = np.select(
        conditions, choices, default='NaN')
    decision = historyDataFrame.iloc[-1, -1]
    return decision



def getVWAP(historyDataFrame):
    historyDataFrame['TP'] = (
        historyDataFrame['high'] + historyDataFrame['low'] + historyDataFrame['close']) / 3
    historyDataFrame['timeFrameTotal'] = historyDataFrame['TP'] * \
        historyDataFrame['volume']
    historyDataFrame['VWAP'] = historyDataFrame['timeFrameTotal'].cumsum(
    ) / historyDataFrame['volume'].cumsum()

    TP = historyDataFrame['TP']

    conditions = [
        (historyDataFrame['VWAP'] < TP),
        (historyDataFrame['VWAP'] > TP),
        (historyDataFrame['VWAP'] == TP)]

    choices = ['SELL', 'BUY', 'HOLD']

    historyDataFrame['decision_VWAP'] = np.select(
        conditions, choices, default='NaN')
    decision = historyDataFrame.iloc[-1, -1]
    return decision
