import numpy as nu
import pandas as pd
import multiprocessing as mp
from matplotlib import pyplot as pl
from mpl_toolkits.mplot3d import axes3d
# self-made class
from LinearInterpolatorClass import LinearInterpolator
from Spot4DClass import Spot4D


class VisibleWeatherData():

    # class properties
    longitudeMargin = 5.0
    latitudeMargin = 5.0
    altitudeMargin = 10.0


    def __init__(self, interpolator, centerSpot, sampleAmount=10):
        # get boundaries
        longitudeLowerBound, longitudeUpperBound, latitudeLowerBound, latitudeUpperBound, altitudeLowerBound, altitudeUpperBound = centerSpot.getSurroundingLongitudeLatitudeAltitudeBoundary(longitudeMargin=VisibleWeatherData.longitudeMargin, latitudeMargin=VisibleWeatherData.latitudeMargin)

        # get grids
        longitudes = nu.linspace(longitudeLowerBound, longitudeUpperBound, sampleAmount)
        latitudes = nu.linspace(latitudeLowerBound, latitudeUpperBound, sampleAmount)
        altitudes = nu.linspace(altitudeLowerBound, altitudeUpperBound, sampleAmount)
        spotsNdarray = nu.zeros((sampleAmount*sampleAmount*sampleAmount, 6)) # longitude, latitude, altitude, time, uWinds, vWinds
        count = 0
        for longitude in longitudes:
            for latitude in latitudes:
                for altitude in altitudes:
                    spotsNdarray[count, :4] = [longitude, latitude, altitude, (centerSpot.time-interpolator.timeStandard).total_seconds()]
                    count += 1

        uWinds, vWinds = interpolator.predictFromSpots_ndarray(spotsNdarray=spotsNdarray[:, :4])
        spotsNdarray[:, 4], spotsNdarray[:, 5] = uWinds, vWinds

        # self.df = pd.DataFrame(spotsNdarray, columns=['longitude', 'latitude', 'altitude', 'timeDelta', 'uWinds', 'vWinds']).fillna(0.0)
        self.df = pd.DataFrame(spotsNdarray, columns=['longitude', 'latitude', 'altitude', 'timeDelta', 'uWinds', 'vWinds']).dropna()


    def plotWinds(self):
        x = self.df['longitude']
        y = self.df['latitude']
        z = self.df['altitude']

        u = self.df['uWinds']
        v = self.df['vWinds']
        w = 0

        fig = pl.figure()
        # ax = fig.add_subplot(projection='3d')
        ax = pl.axes(projection='3d')
        # https://matplotlib.org/stable/gallery/mplot3d/quiver3d.html
        ax.quiver(x, y, z, u, v, w, length=0.03, arrow_length_ratio = 0.8)
        pl.show()
