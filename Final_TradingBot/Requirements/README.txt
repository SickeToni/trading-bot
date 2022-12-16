Infos:
The RealtimeBot takes historydata by opening the connection to the websocket, after recieving the first realtime candlestick, it is able to calculate the TAIs right away.
The recieved history- and realtimedata will be stored in a MongoDB as well as the decisions(BUY,SELL,HOLD) from the TAIs.
If the majority of the TAIs calculate the same decision, it will be executed( SELL, BUY, HOLD).

In case of recieving the same decsion multiple times in a row, the bot will HOLD and waits until there is an other decision incoming which is different to the last executed one.
After executing a trade, it will send a message on your telegram bot.

https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#klinecandlestick-streams




Environment:
VS Code https://code.visualstudio.com/download

Dependencies:

1. Python 3.10.0 from https://www.python.org/downloads/
2. Python Extension in VS Code
3. Virtual Environment in VS Code:https://predictivehacks.com/how-to-work-with-vs-code-and-virtual-environments-in-python/
3. pip version: pip 21.3.1 
    included in python 3.10.0 (Set Pathvariable)
4. Create a Binance API and paste the keys in the "config_real" file: https://www.binance.com/en/support/faq/360002502072
5. Setup a Mongo DB on your local machine  https://www.mongodb.com/try
6. Telegram Bot: https://medium.com/@robertbracco1/how-to-write-a-telegram-bot-to-send-messages-with-python-bcdf45d0a580



Libraries:

(install with: pip install "Library")

Pandas
TA-Lib (0.4.21) # https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib (Paste the .whl file in the folder where Python 3.10.0 is)

python-binance (1.0.15)

numpy (1.21.3)

websocket_client (1.2.1)

binance.client (1.0.0)
    -binance.enums

pymongo (4.0)

telegram-send (0.25)

json

csv         


