import importlib
import time
import threading
import pandas as pd
from GetHistory import CrpytoCompare
from datetime import datetime

class Follower(object):
    def __init__(self, live_sleep_secs=10, hist_sleep_secs=60, leader='BTC', follower='ETH', quote='USD',
                 lead_exchange='Bitfinex', follow_exchange='Bitfinex', std_deviations=7, mins_to_wait=5,
                 order_size='0.01'):
        # Settings
        self.leader = leader
        self.follower = follower
        self.quote = quote
        self.lead_exchange = lead_exchange
        self.follow_exchange = follow_exchange
        leader_module = importlib.import_module("Markets." + lead_exchange)
        follower_module = importlib.import_module("Markets." + follow_exchange)
        self.leader_public = leader_module.Client()
        self.follower_public = follower_module.Client()
        #self.leader_trade = leader_module.TradeClient()
        self.follower_trade = follower_module.TradeClient()
        self.live_sleep_secs = live_sleep_secs
        self.hist_sleep_secs = hist_sleep_secs
        self.std_deviations = std_deviations
        self.mins_to_wait = mins_to_wait
        self.order_size = order_size
        self.close_order = {'buy': 'sell', 'sell': 'buy'}
        self.print = True

        # Data
        self.history = pd.DataFrame
        self.livePrice = {'leader': {'bid': 0, 'ask': 0}, 'follower': {'bid': 0, 'ask': 0}}
        self.target_delta = 0
        self.last_ratio = 0
        self.current_delta = 0
        self.history_loaded = False

        # Actions
        self.start_history_thread()
        self.start_live_thread()
        self.run_loop()

    def get_history(self, base, quote, exchange):
        return CrpytoCompare.fetch_crypto_close(base, quote, exchange)

    def refresh_target(self):
        self.history['ratio'] = self.history.leader / self.history.follower
        self.history['delta'] = self.history.ratio.diff()
        self.target_delta = self.history['delta'].std() * self.std_deviations
        self.last_ratio = self.history['ratio'][-1]
        #CrpytoCompare.save_history_file('base', 'base', 'exchange', 'histominute', self.history)

    def refresh_current(self):
        current_ratio = ((self.livePrice['leader']['ask'] + self.livePrice['leader']['bid']) / 2) / \
                             ((self.livePrice['follower']['ask'] + self.livePrice['follower']['bid']) / 2)
        self.current_delta = current_ratio - self.last_ratio

    def refresh_history(self):
        leader_history = self.get_history(self.leader, self.quote, self.lead_exchange)
        leader_history.columns = ['leader']
        follower_history = self.get_history(self.follower, self.quote, self.follow_exchange)
        follower_history.columns = ['follower']
        self.history = pd.concat([leader_history, follower_history], axis=1, join='inner')
        self.history_loaded = True

    def history_worker(self):
        while 1:
            self.refresh_history()
            self.refresh_target()
            time.sleep(self.hist_sleep_secs)

    def start_history_thread(self):
        t = threading.Thread(target=self.history_worker)
        t.daemon = True
        t.start()

    def live_worker(self):
        while 1:
            if self.history_loaded:
                self.get_live_price()
                self.refresh_current()
                self.trade_trigger()
                time.sleep(self.live_sleep_secs)

    def get_live_price(self):
        leader_response = self.leader_public.ticker(self.leader + self.quote)
        follower_response = self.follower_public.ticker(self.follower + self.quote)
        self.livePrice = {'leader': {'bid': leader_response['bid'], 'ask': leader_response['ask']},
                          'follower': {'bid': follower_response['bid'], 'ask': follower_response['ask']}}

    def start_live_thread(self):
        t = threading.Thread(target=self.live_worker)
        t.daemon = True
        t.start()

    def trade_trigger(self):
        if self.target_delta <= abs(self.current_delta) and self.current_delta > 0:
            self.execute(['buy', 'sell'])
        elif self.target_delta <= abs(self.current_delta) and self.current_delta < 0:
            self.execute(['sell', 'buy'])
        elif datetime.today().minute % 10 == 0 and self.print == True:
            print('%s - current: %.4f, target: %.4f' % (datetime.today(), self.current_delta, self.target_delta))
            self.print = False
        elif datetime.today().minute % 11 == 0 and self.print == False:
            self.print = True

    def execute(self, order):
        time_stamp = int(datetime.today().timestamp())
        print(self.follower_trade.place_order(self.order_size, '1', order[0], 'market', self.follower + self.quote))
        time.sleep(self.mins_to_wait*60)
        print(self.follower_trade.place_order(self.order_size, '1', order[1], 'market', self.follower + self.quote))
        print(self.calc_pnl(time_stamp))

    def run_loop(self):
        while 1:
            pass
        #l = 1
        #while l < 3:
        #    l += 1
        #    time.sleep(10)
        #    print('Leader: %.4f, %.4f' % (self.livePrice['leader']['ask'], self.livePrice['leader']['bid']))
        #    print('Follower: %.4f, %.4f' % (self.livePrice['follower']['ask'], self.livePrice['follower']['bid']))
        #    print('CurrentDelta: %.4f, TargetDelta: %.4f' % (self.current_delta, self.target_delta))
        #    print('\n========------Next Loop------========')

    def calc_pnl(self, time_stamp):
        trades = self.follower_trade.past_trades(time_stamp, self.follower + self.quote)
        fee, pnl = 0, 0
        buy_sell = {'Buy': -1, 'Sell': 1}
        for t in trades:
            fee += float(t['fee_amount'])
            pnl += float(t['price']) * float(t['amount']) * float(buy_sell[t['type']])
        return {'fee': fee, 'pnl': pnl, 'net': pnl + fee}


from Markets import Bitfinex


def test_api(side):
    trade = Bitfinex.TradeClient()
    #print(trade.place_order('0.01', '1', 'buy, 'market', 'ethusd'))
    print(trade.active_positions())
    #print(trade.place_order('0.01', '200', 'sell', 'stop', 'ethusd'))

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


if __name__ == '__main__':
    f = Follower(std_deviations=7)
    #test_api('sell')
    #print(calc_pnl(1501700966))



