from GetHistory.CrpytoCompare import *
#import pandas as pd

def hdf5_to_csv(fsym, tsym, exchange, granularity):
    df = find_history_file(fsym, tsym, exchange, granularity)
    df.to_csv()