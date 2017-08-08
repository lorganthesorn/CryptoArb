import numpy as np
import pandas as pd
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests
import os


def timestamp2datetime(timestamp):
    # function converts a Unix timestamp into Gregorian date
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')


def date2timestamp(date):
    # function coverts Gregorian date in a given format to timestamp
    return datetime.strptime(str(date),'%Y-%m-%d %H:%M:%S').timestamp()


def find_history_file(fsym, tsym, exchange, granularity):
    f = os.path.dirname(__file__) + '\\HistoryData\\' + granularity + '\\' + fsym + '_' + tsym + '.h5'
    return pd.read_hdf(f.strip('.'), 'data')


def sort_remove_duplicates(data):
    data = data.reset_index().drop_duplicates(subset='date', keep='last').set_index('date')
    data = data.sort_index()
    data = data.convert_objects(convert_numeric=True)
    return data


def save_history_file(fsym, tsym, exchange, granularity, data):
    path = os.path.dirname(__file__) + '\\HistoryData\\' + granularity + '\\' + fsym + '_' + tsym
    #path = 'C:\\Users\\caspreckley\\Desktop\\' + fsym + '_' + tsym
    store = pd.HDFStore(path + '.h5')
    store['data'] = data
    store.close()
    data.to_csv(path + '.csv')


def fetch_crypto_close(fsym, tsym, exchange, granularity='histominute', data=None):
    # function fetches the close-price time-series from cryptocompare.com
    # it may ignore near-zero pricing
    cols = ['date', 'timestamp', exchange]
    lst = ['time', 'open', 'high', 'low', 'close']

    timestamp_today = datetime.today().timestamp()
    if data is None:
        try:
            data = find_history_file(fsym, tsym, exchange, granularity)
            mins = int((timestamp_today - date2timestamp(data.index[-1])) / 60) + 1
            loops = int(mins / 2000)
        except FileNotFoundError:
            loops = 5
            mins = 2000
    else:
        mins = int((timestamp_today - date2timestamp(data.index[-1])) / 60) + 1
        loops = int(mins / 2000)

    curr_timestamp = timestamp_today

    for j in range(max(loops, 1)):
        df = pd.DataFrame(columns=cols)
        url = "https://min-api.cryptocompare.com/data/"+granularity+"?fsym=" + fsym + \
              "&tsym=" + tsym + "&toTs=" + str(int(curr_timestamp)) + "&limit="+str(mins)+"&e=" + exchange
        #print(url)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        dic = json.loads(soup.prettify())
        for i in range(1, mins+1):
            tmp = []
            for e in enumerate(lst):
                x = e[0]
                y = dic['Data'][i][e[1]]
                if(x == 0):
                    tmp.append(str(timestamp2datetime(y)))
                tmp.append(y)
            if(np.sum(tmp[-4::]) > 0):  # remove for near zero vals
                tmp = np.array(tmp)
                tmp = tmp[[0,1,5]]  # filter solely for close prices
                df.loc[len(df)] = np.array(tmp)
        # ensure a correct date format
        df.index = pd.to_datetime(df.date, format="%Y-%m-%d %H:%M:%S")
        df.drop('date', axis=1, inplace=True)
        curr_timestamp = date2timestamp(df.index[0])
        if j == 0 and data is None:
            data = df.copy()
        else:
            data = pd.concat([df, data], axis=0)
    data.drop("timestamp", axis=1, inplace=True)
    data = sort_remove_duplicates(data)
    save_history_file(fsym, tsym, exchange, granularity, data)
    return data # DataFrame


def crypto_close(fsym, tsym, exchange, granularity='histominute'):
    # function fetches the close-price time-series from cryptocompare.com
    # it may ignore near-zero pricing
    cols = ['date', 'timestamp', exchange]
    lst = ['time', 'open', 'high', 'low', 'close']

    timestamp_today = datetime.today().timestamp()
    curr_timestamp = timestamp_today

    for j in range(5):
        df = pd.DataFrame(columns=cols)
        url = "https://min-api.cryptocompare.com/data/"+granularity+"?fsym=" + fsym + \
              "&tsym=" + tsym + "&toTs=" + str(int(curr_timestamp)) + "&limit=2000&e=" + exchange
        #print(url)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        dic = json.loads(soup.prettify())
        for i in range(1, 2001):
            tmp = []
            for e in enumerate(lst):
                x = e[0]
                y = dic['Data'][i][e[1]]
                if(x == 0):
                    tmp.append(str(timestamp2datetime(y)))
                tmp.append(y)
            if(np.sum(tmp[-4::]) > 0):  # remove for near zero vals
                tmp = np.array(tmp)
                tmp = tmp[[0,1,5]]  # filter solely for close prices
                df.loc[len(df)] = np.array(tmp)
        # ensure a correct date format
        df.index = pd.to_datetime(df.date, format="%Y-%m-%d %H:%M:%S")
        df.drop('date', axis=1, inplace=True)
        curr_timestamp = date2timestamp(df.index[0])
        if j == 0:
            data = df.copy()
        else:
            data = pd.concat([df, data], axis=0)
    data.drop("timestamp", axis=1, inplace=True)
    data = sort_remove_duplicates(data)
    return data # DataFrame


def fetch_top_exchanges(fsym, tsym):
    pass


def get_top_exchanges(fsym, tsym, limit='10'):
    url = "https://min-api.cryptocompare.com/data/top/exchanges?fsym=" + fsym + \
              "&tsym=" + tsym + "&limit=" + limit
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    dic = json.loads(soup.prettify())
    exchanges = {e['exchange']: e['volume24h'] for e in dic['Data']}
    return exchanges


def get_coins_by_marketcap(size=50e6):
    url = "https://api.coinmarketcap.com/v1/ticker/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    dic = json.loads(soup.prettify())

    df = pd.DataFrame(columns=["Ticker", "MarketCap"])
    for i in range(len(dic)):
        df.loc[len(df)] = [dic[i]['symbol'], dic[i]['market_cap_usd']]

    df.sort_values(by=['MarketCap'])
    df.MarketCap = pd.to_numeric(df.MarketCap)
    p = df[df.MarketCap > size]
    return list(p.Ticker)


def fetch_liquidity(fsym, tsym, exchange="All"):
    pass

if __name__ == '__main__':
    #fetch_crypto_close('BTC', 'USD', 'Bitfinex', granularity='histominute', data=None)
    #data = getTopExchanges('BTC', 'USD', '10')
    #print([data.keys()])
    #for i in data.keys():
    #    print('%s: %.f' % (i, data[i]))
    get_coins_by_marketcap()



