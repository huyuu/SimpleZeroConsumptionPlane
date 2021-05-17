import numpy as nu
from matplotlib import pyplot as pl
import pandas as pd




class WindDrawer():
    def __init__(self):
        pass

    def plotWinds(self, visibleWeatherData):
        x = visibleWeatherData.df['longitude']
        y = visibleWeatherData.df['latitude']
        z = visibleWeatherData.df['altitude']

        u = visibleWeatherData.df['uWinds']
        v = visibleWeatherData.df['vWinds']
        w = 0

        ax = plt.figure().add_subplot(projection='3d')
        ax.quiver(x, y, z, u, v, w)
        pl.show()
