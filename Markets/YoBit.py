#from urllib import Request, urlopen
#from pprint import pprint
import json
import time
import requests
import hmac
import hashlib
#from urllib3 import urlencode

class Yobit(object):

    def __init__(self, key, secret):
        self.key = 'mykey'
        self.secret = b'mysecret'
        self.public = ['info', 'ticker', 'depth', 'trades']
        self.trade = ['activeorders']

    def query(self, method, values=[]):
        if method in self.public:
            url = 'https://yobit.net/api/3/'+method
            for i in values:
                url += '/'+i

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

            req = requests.post(url,data=values,headers=headers)
            return json.loads(req.text)

        return False

    def getTickers(self):
        self.query(self, 'info')['pairs']


    def returnOrderBook(self, ticker):
        return self.query('depth', [ticker])[ticker]

