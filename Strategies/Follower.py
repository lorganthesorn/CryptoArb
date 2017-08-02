import importlib
import time
import threading
import pandas as pd
from GetHistory import CrpytoCompare


class Follower(object):
    def __init__(self, ma_period=30, sleep_secs=10, hist_sleep_secs=60, leader='BTC', follower='ETH', quote='USD',
                 leadExchange='Bitfinex', followExchange='Bitfinex', std_deviations=7, mins_to_wait=5):
        # Settings
        self.leader = leader
        self.follower = follower
        self.quote = quote
        self.leadExchange = leadExchange
        self.followExchange = followExchange
        leaderModule = importlib.import_module("Markets." + leadExchange)
        followerModule = importlib.import_module("Markets." + followExchange)
        self.leaderAPI = leaderModule.Client()
        self.followerAPI = followerModule.Client()
        self.ma_period = ma_period
        self.sleep_secs = sleep_secs
        self.hist_sleep_secs = hist_sleep_secs
        self.std_deviations = std_deviations
        self.mins_to_wait = mins_to_wait

        # Data
        self.leaderHistory = pd.DataFrame()
        self.followerHistory = pd.DataFrame()
        self.livePrice = {'leader': {'bid': 0, 'ask': 0}, 'follower': {'bid': 0, 'ask': 0}}
        self.current_diff = 0
        self.std_dev = 0

        # Actions
        self.start_history_thread()
        self.start_live_thread()
        self.run_loop()

    def get_history(self, base, quote, exchange):
        return CrpytoCompare.fetch_crypto_close(base, quote, exchange)

    def refresh_ma(self):
        df = pd.DataFrame(columns=['ratio', 'ma', 'diff'])
        df['ratio'] = self.leaderHistory / self.followerHistory
        #df['ma'] = df['ratio'].rolling(window=self.ma_period).mean()
        #df['diff'] = df['ratio'] - df['diff']
        self.std_dev = df['ratio'].std()
        self.current_ma = df['ma'][-1]
        self.current_diff = df['diff'][-1]

    def refresh_history(self):
        self.leaderHistory = self.get_history(self.leader, self.quote, self.leadExchange)
        self.followerHistory = self.get_history(self.follower, self.quote, self.followExchange)

    def history_worker(self):
        while 1:
            self.refresh_history()
            self.refresh_ma()
            time.sleep(self.hist_sleep_secs)

    def start_history_thread(self):
        t = threading.Thread(target=self.history_worker)
        t.daemon = True
        t.start()

    def live_worker(self):
        while 1:
            self.get_live_price()
            time.sleep(self.sleep_secs)

    def get_live_price(self):
        leaderResponse = self.leaderAPI.ticker(self.leader + self.quote)
        followerResponse = self.followerAPI.ticker(self.follower + self.quote)
        self.livePrice = {'leader':  {'bid': leaderResponse['bid'], 'ask': leaderResponse['ask']},
                          'follower': {'bid': followerResponse['bid'], 'ask': followerResponse['ask']}}

    def start_live_thread(self):
        t = threading.Thread(target=self.live_worker)
        t.daemon = True
        t.start()

    def get_expected_ratio(self):
        #in the case where ratio is trending may be required
        pass

    def trade_trigger(self):

        pass

    def execute(self):
        pass

    def run_loop(self):
        l = 1
        while l < 10:
            l += 1
            time.sleep(10)
            #print('Leader MA: %.4f' % self.leaderMA.iloc[-1][-1])
            #print('Follower MA: %.4f' % self.followerMA.iloc[-1][-1])

            print('Leader ask: %.4f' % self.livePrice['leader']['ask'])
            print('Follower ask: %.4f' % self.livePrice['follower']['ask'])

            print('\n========------Next Loop------========')


if __name__ == '__main__':
    f = Follower()
