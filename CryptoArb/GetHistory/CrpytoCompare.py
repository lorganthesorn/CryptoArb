import numpy as np
import pandas as pd
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests


def timestamp2datetime(timestamp):
    # function converts a Unix timestamp into Gregorian date
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')


def date2timestamp(date):
    # function coverts Gregorian date in a given format to timestamp
    return datetime.strptime(date, '%Y-%m-%d').timestamp()


def fetch_crypto_close(fsym, tsym, exchange):
    # function fetches the close-price time-series from cryptocompare.com
    # it may ignore near-zero pricing
    cols = ['date', 'timestamp', exchange]
    lst = ['time', 'open', 'high', 'low', 'close']
    timestamp_today = datetime.today().timestamp()
    curr_timestamp = timestamp_today

    for j in range(5):
        df = pd.DataFrame(columns=cols)
        url = "https://min-api.cryptocompare.com/data/histominute?fsym=" + fsym + \
              "&tsym=" + tsym + "&toTs=" + str(int(curr_timestamp)) + "&limit=2000&e=" + exchange
        # print(url)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        dic = json.loads(soup.prettify())
        for i in range(1, 2001):
            tmp = []
            for e in enumerate(lst):
                x = e[0]
                y = dic['Data'][i][e[1]]
                if (x == 0):
                    tmp.append(str(timestamp2datetime(y)))
                tmp.append(y)
            if (np.sum(tmp[-4::]) > 0):  # remove for USDT
                tmp = np.array(tmp)
                tmp = tmp[[0, 1, 4]]  # filter solely for close prices
                df.loc[len(df)] = np.array(tmp)
        # ensure a correct date format
        df.index = pd.to_datetime(df.date, format="%Y-%m-%d %H:%M:%S")
        df.drop('date', axis=1, inplace=True)
        curr_timestamp = int(df.ix[0][0])
        if (j == 0):
            data = df.copy()
        else:
            data = pd.concat([df, data], axis=0)
    data.drop("timestamp", axis=1, inplace=True)
    return data  # DataFrame


def fetch_top_exchanges(fsym, tsym, limit=15):
    url = "https://min-api.cryptocompare.com/data/top/exchanges?fsym=" + fsym + \
          "&tsym=" + tsym + "&limit=" + limit
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    dic = json.loads(soup.prettify())
    exchanges = {e['exchange']: e['volume24h'] for e in dic['Data']}
    return exchanges


def fetch_liquidity(fsym, tsym, exchange="All"):
    pass



