from Markets import Bitfinex

def test_api(side):
    #trade = Bitfinex.TradeClient()
    #print(trade.place_order('0.01', '1', 'buy, 'market', 'ethusd'))
    #print(trade.active_positions())
    #print(trade.place_order('0.01', '200', 'sell', 'stop', 'ethusd'))
    # for testing - self.execute(['buy', 'sell'])

    x = trade.past_trades(1501700966, 'ethusd')
    print(x['fee_amount'])
    print(x[''])

def calc_pnl(time_stamp):
    trade = Bitfinex.TradeClient()
    trades = trade.past_trades(time_stamp, 'ethusd')
    fee, pnl = 0, 0
    buysell = {'Buy': -1, 'Sell': 1}
    for t in trades:
        fee += float(t['fee_amount'])
        pnl += float(t['price']) * float(t['amount']) * float(buysell[t['type']])
    return {'fee': fee, 'pnl': pnl, 'net': pnl+fee}

