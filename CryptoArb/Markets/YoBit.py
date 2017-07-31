import time
import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode
from Markets.Market import Market


class Yobit(Market):
    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret
        self.public = ['info', 'ticker', 'depth', 'trades']
        self.trade = ['activeorders']

    def query(self, method, values):
        if method in self.public:
            url = 'https://yobit.net/api/3/'+method
            for k in values:
                url += '/'+k
            req = requests.get(url)
            return json.loads(req.text)

        elif method in self.trade:
            url = 'https://yobit.net/tapi'
            values['method'] = method
            values['nonce'] = str(int(time.time()))
            body = urlencode(values)
            signature = hmac.new(self.secret, body, hashlib.sha512).hexdigest()
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.key,
                'Sign': signature
            }

            req = requests.post(url,data=values, headers=headers)
            return json.loads(req.text)

        return False

    def get_depth(self, fsym, tsym):
        return self.query('depth', [fsym+'_'+tsym])
