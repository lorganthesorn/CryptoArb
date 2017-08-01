from Markets import Poloniex
from Markets import YoBit

p = Poloniex.Poloniex(None, None)
y = YoBit.Yobit(None, None)

pPairs = [i for i in p.returnTicker().keys()]
yPairs = [i for i in y.query('info')['pairs'].keys()]

pPairs.sort()
yPairs.sort()

for yo in yPairs:
    if 'dash_btc' in yo:
        print(y.returnOrderBook(yo))

for po in pPairs:
    if 'BTC_DASH' in po:
        print(p.returnOrderBook(po))

