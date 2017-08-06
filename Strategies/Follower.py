import importlib
import time
import threading
import pandas as pd
import os
from requests import exceptions
from json import decoder
from GetHistory import CrpytoCompare
from datetime import datetime, timedelta
from Markets import APIKeys


class Follower(object):
    def __init__(self, live_sleep_secs=10, hist_sleep_secs=60, leader='BTC', follower='ETH', quote='USD',
                 lead_exchange='Bitfinex', follow_exchange='Bitfinex', std_deviations=7, mins_to_wait=5,
                 order_size='0.01', history_days=5, stop_loss='0.75'):
        # Settings
        self.leader = leader
        self.follower = follower
        self.quote = quote
        self.lead_exchange = lead_exchange
        self.follow_exchange = follow_exchange
        leader_module = importlib.import_module("Markets." + lead_exchange)
        follower_module = importlib.import_module("Markets." + follow_exchange)
        follower_keys = getattr(APIKeys, follow_exchange)
        self.leader_public = leader_module.Client()
        self.follower_public = follower_module.Client()
        self.follower_trade = follower_module.TradeClient(key=follower_keys['key'], secret=follower_keys['secret'])
        self.live_sleep_secs = live_sleep_secs
        self.hist_sleep_secs = hist_sleep_secs
        self.std_deviations = std_deviations
        self.mins_to_wait = mins_to_wait
        self.order_size = order_size
        self.close_order = {'buy': 'sell', 'sell': 'buy'}
        self.print = True
        self.log_file = open(os.path.dirname(__file__) + '/Log/FollowerLog'+follower+'.txt', 'a')
        self.open_order = False
        self.start_date = datetime.today() - timedelta(days=history_days)
        self.stop_loss = stop_loss
        self.last_trade_time = datetime.today().timestamp()

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
        self.start_log_thread()
        self.run_loop()

    def get_history(self, base, quote, exchange):
        return CrpytoCompare.fetch_crypto_close(base, quote, exchange)

    def refresh_target(self):
        self.history['ratio'] = self.history.leader[self.start_date: datetime.today()] / \
                                self.history.follower[self.start_date: datetime.today()]
        self.history['delta'] = self.history.ratio.diff()
        self.target_delta = self.history['delta'].std() * self.std_deviations
        self.last_ratio = self.history['ratio'][-2]
        CrpytoCompare.save_history_file('base', 'base', 'exchange', 'histominute', self.history)

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

    def start_log_thread(self):
        t = threading.Thread(target=self.write_to_log)
        t.daemon = True
        t.start()

    def write_to_log(self):
        while 1:
            if self.history_loaded:
                self.log_file.write('\n%s,%s,%s,%s,%s,%s' % (datetime.today(), self.livePrice['leader']['ask'],
                                    self.livePrice['follower']['ask'], self.target_delta,
                                    abs(self.current_delta), self.open_order))
                try:
                    self.log_file.flush()
                except PermissionError:
                    print('PermissionError on log file: %s' % datetime.today())
            time.sleep(10)

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
        try:
            leader_response = self.leader_public.ticker(self.leader + self.quote)
            follower_response = self.follower_public.ticker(self.follower + self.quote)
            self.livePrice = {'leader': {'bid': leader_response['bid'], 'ask': leader_response['ask']},
                              'follower': {'bid': follower_response['bid'], 'ask': follower_response['ask']}}
        except exceptions.ReadTimeout:
            print('ReadTimeout in live price feed: %s' % datetime.today())
        except decoder.JSONDecodeError:
            print('JSONDecodeError in live price feed: %s' % datetime.today())

    def start_live_thread(self):
        t = threading.Thread(target=self.live_worker)
        t.daemon = True
        t.start()

    def get_active_positions(self):
        try:
            return len(self.follower_trade.active_positions())
        except decoder.JSONDecodeError:
            print('JSONDecode error in active order check %s' % datetime.today())
            return 1

    def trade_trigger(self):
        if self.get_active_positions() != 0:
            return
        elif self.open_order:
            self.open_order = False
            print(self.calc_pnl())
        if self.target_delta <= abs(self.current_delta) and self.current_delta > 0:
            self.execute(['buy', 'sell'])
        elif self.target_delta <= abs(self.current_delta) and self.current_delta < 0:
            self.execute(['sell', 'buy'])

    def execute(self, order):
        self.last_trade_time = int(datetime.today().timestamp())
        print(self.follower_trade.place_order(self.order_size, '1', order[0], 'market', self.follower + self.quote))
        print(self.follower_trade.place_order(self.order_size, self.stop_loss, order[1], 'trailing-stop', self.follower + self.quote))
        self.open_order = True
        #time.sleep(self.mins_to_wait*60)
        #self.open_order = False
        #print(self.follower_trade.place_order(self.order_size, '1', order[1], 'market', self.follower + self.quote))

    def run_loop(self):
        while 1:
            print('Follower strategy running - type "close" to exit')
            if input() == 'close':
                self.log_file.close()
                return

    def calc_pnl(self):
        trades = self.follower_trade.past_trades(self.last_trade_time, self.follower + self.quote)[-2:]
        fee, pnl = 0, 0
        buy_sell = {'Buy': -1, 'Sell': 1}
        for t in trades:
            fee += float(t['fee_amount'])
            pnl += float(t['price']) * float(t['amount']) * buy_sell[t['type']]
        return {'fee': fee, 'pnl': pnl, 'net': pnl + fee}


if __name__ == '__main__':
    f = Follower(history_days=2, follower='XMR', order_size='0.1')
