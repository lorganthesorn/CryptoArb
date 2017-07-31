import importlib
from GetHistory import CrpytoCompare

class Follower(object):
    def __init__(self, leader='BTC', follower='ETH', leadExchange='Bitfinex', followExchange='Bitfinex'):
        self.leader = leader
        self.follower = follower
        self.leadExchange = leadExchange
        self.followExchange = followExchange
        leaderModule = importlib.import_module("Markets." + leadExchange)
        followerModule = importlib.import_module("Markets." + followExchange)
        self.leaderAPI = leaderModule.Client()
        self.followerAPI = followerModule.Client()


    def get_history(self):
        CrpytoCompare.fetch_crypto_close(self.leader, 'USD', self.leadExchange)


if __name__ == '__main__':
    f = Follower()
    f.get_history()