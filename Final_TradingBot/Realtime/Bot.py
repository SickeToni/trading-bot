
import json
from numpy import single
import pymongo
from pymongo import message
import websocket
import json
import pandas as pd
from binance.client import Client
from binance.enums import *
from csv import writer
from TAI import getEMA, getVWAP
from TAI import getRSI
import config_real
import telegram_send

#######################################################################################

TRADE_SYMBOL = "BTCBUSD"
TRADE_QUANTITY = 100


#######################################################################################


client = Client(config_real.API_KEY, config_real.API_SECRET)


SOCKET = "wss://stream.binance.com:9443/ws/{}@kline_1m".format(
    TRADE_SYMBOL.lower())


myclient = pymongo.MongoClient("mongodb://localhost:27017/") #Individual




mydb = myclient["TradingBot"]
candleData = mydb["candleData"]
tradingHistoryRaw = mydb["tradingHistoryRaw"]
tradingHistoryReal = mydb["tradingHistoryReal"]
orderBook = mydb["orderBook"]


in_position = False


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_test_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
        decisionToJson = {
            "Order": str(order)
        }

        orderBook.insert_one(decisionToJson)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True


def on_open(ws):

    print('opened connection')
    for candlestick in client.get_historical_klines_generator(TRADE_SYMBOL, Client.KLINE_INTERVAL_1MINUTE, "10 day ago UTC"):
        candlestick[0] = candlestick[0] / 1000
        toJson = [candlestick[0], candlestick[4],
                  candlestick[2], candlestick[3], candlestick[5]]
      
        historcalJsonToDBstructure = {
            "time": float(candlestick[0]),
            "close": float(candlestick[4]),
            "high": float(candlestick[2]),
            "low": float(candlestick[3]),
            "volume": float(candlestick[5])
        }
        candleData.insert_one(historcalJsonToDBstructure)


def on_close(ws):
    candleData.drop()
    print('closed connection')
    print('CandleData deleted')


def checkLastTrade(checkedFinalDecision):
    count = tradingHistoryReal.count_documents({})
    if count != 0:
        mydoc = tradingHistoryRaw.find().sort("_id", -1).limit(1)
        entry = mydoc[0]
        lastDecision = entry['Decision']

        if lastDecision != checkedFinalDecision:
            return checkedFinalDecision
        else:

            return "HOLD"
    else:
        print("counter is null")
        return checkedFinalDecision


def on_message(ws, message):
    global closes, in_position
    json_message = json.loads(message)  
    candle = json_message['k']  

    is_candle_closed = candle['x']

    if is_candle_closed:
        mydict = candle
        currentJsonToDBstructure = {
            "time": float(candle['T']),
            "close": float(candle['c']),
            "high": float(candle['h']),
            "low": float(candle['l']),
            "volume": float(candle['v']),
        }
        candleData.insert_one(currentJsonToDBstructure)
        historyDataFrame = pd.DataFrame(list(candleData.find().sort("_id", -1).limit(200)))
        historyDataFrame = historyDataFrame.sort_values('_id', ascending=True)
        decisionRSI = getRSI(historyDataFrame)
        decisionEMA = getEMA(historyDataFrame)
        decisionVWAP = getVWAP(historyDataFrame)
        closingPrice = float(candle['c'])
        if decisionRSI == decisionEMA:
            finalDecision = decisionRSI
        elif decisionRSI == decisionVWAP:
            finalDecision = decisionRSI
        elif decisionEMA == decisionVWAP:
            finalDecision = decisionEMA
        else:
            finalDecision = "HOLD"
      
        finalDecision = "BUY"
        
        print("RSI:", decisionRSI, "EMA:", decisionEMA, "VWAP:", decisionVWAP)
        print("Closing Price", closingPrice)
        if finalDecision != "HOLD":
            tradeOrder = checkLastTrade(finalDecision)

            decisionToJsonRaw = {
                "Decision": str(finalDecision)
            }

            tradingHistoryRaw.insert_one(decisionToJsonRaw)

            decisionToJsonReal = {
                "Decision": str(tradeOrder)
            }

            tradingHistoryReal.insert_one(decisionToJsonReal)
        else:
            tradeOrder = "HOLD"

        if tradeOrder == "SELL":
            if in_position:
                success = order(SIDE_SELL, TRADE_QUANTITY,
                                TRADE_SYMBOL, order_type=ORDER_TYPE_MARKET)
                telegram_send.send(messages=["Sold {}".format(TRADE_SYMBOL), "for:{}".format(closingPrice)])
                if success:
                    in_position = False
            else:
                print("No order placed!")

        elif tradeOrder == "BUY":
            if in_position:
                print("No order placed!")
            else:
                success = order(SIDE_SELL, TRADE_QUANTITY,
                                TRADE_SYMBOL, order_type=ORDER_TYPE_MARKET)
                telegram_send.send(messages=["Bought {}".format(TRADE_SYMBOL), "for:{}".format(closingPrice)])

        print("Final Decision: ", tradeOrder)
        closingPriceToInt = float(closingPrice)
# -----------------------------------------------------------------------------------------------------------------------------
        closes = closingPriceToInt
        rsi = decisionRSI
        ema = decisionEMA
        vwap = decisionVWAP
        finalDecisions = tradeOrder
        times = (float(candle['T']))

        global listForCalculation
        listForCalculation = [times, rsi, ema, vwap, finalDecisions, closes]

        def append_list_as_row(file_name, list_of_elem):
            with open(file_name, 'a', newline='') as write_obj:
                csv_writer = writer(write_obj)
                csv_writer.writerow(list_of_elem)

        append_list_as_row('decisions_LogFile.csv', listForCalculation)
        print(
            "______________________________________________________________________________")


ws = websocket.WebSocketApp(SOCKET, on_open=on_open,
                            on_close=on_close, on_message=on_message)

ws.run_forever()
