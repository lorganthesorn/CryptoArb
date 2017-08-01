from Markets import Poloniex
from Markets import YoBit

p = Poloniex.Poloniex(None, None)
y = YoBit.Yobit(None, None)

#pPairs = [i for i in p.getTickers().keys()]
#yPairs = [i for i in y.getTickers().keys()]

#pPairs.sort()
#yPairs.sort()

yBook = y.returnOrderBook('dash_btc')
pBook = p.returnOrderBook('BTC_DASH')

yBid, yAsk = float(yBook['bids'][0][0]), float(yBook['asks'][0][0])
pBid, pAsk = float(pBook['bids'][0][0]), float(pBook['asks'][0][0])

print('arb: %0.4f, y: %0.4f, p: %0.4f'%((yAsk - pBid)/pBid, yAsk, pBid))
print('arb: %0.4f, y: %0.4f, p: %0.4f'%((pAsk - yBid)/yBid, pAsk, yBid))


