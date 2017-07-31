import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import datetime
import json
from bs4 import BeautifulSoup
import requests


def correlation(df):
    df1 = df.dropna().drop_duplicates()
    dfP = df1.dropna(axis=1, how='any')

    m = dfP.mean(axis=0)
    s = dfP.std(ddof=1, axis=0)

    # normalised time-series as an input for PCA
    dfPort = (dfP - m)/s

    c = np.cov(dfPort.values.T)     # covariance matrix
    co = np.corrcoef(dfP.values.T)  # correlation matrix

    tickers = list(dfP.columns)


    plt.figure(figsize=(8,8))
    plt.imshow(co, cmap="RdGy", interpolation="nearest")
    cb = plt.colorbar()
    cb.set_label("Correlation Matrix Coefficients")
    plt.title("Correlation Matrix", fontsize=14)
    plt.xticks(np.arange(len(tickers)), tickers, rotation=90)
    plt.yticks(np.arange(len(tickers)), tickers)


def divergence():
    pass


def pca(df):
    df1 = df.dropna().drop_duplicates()
    dfP = df1.dropna(axis=1, how='any')

    m = dfP.mean(axis=0)
    s = dfP.std(ddof=1, axis=0)

    # normalised time-series as an input for PCA
    dfPort = (dfP - m)/s

    c = np.cov(dfPort.values.T)     # covariance matrix
    co = np.corrcoef(dfP.values.T)  # correlation matrix

    tickers = list(dfP.columns)

    # perform PCA
    w, v = np.linalg.eig(c)

    ax = plt.figure(figsize=(8,8)).gca()
    plt.imshow(v, cmap="bwr", interpolation="nearest")
    cb = plt.colorbar()
    plt.yticks(np.arange(len(tickers)), tickers)
    plt.xlabel("PC Number")
    plt.title("PCA", fontsize=14)
    # force x-tickers to be displayed as integers (not floats)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    plt.show()
