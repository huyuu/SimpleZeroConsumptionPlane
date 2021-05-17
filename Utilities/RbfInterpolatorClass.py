import numpy as nu
import pandas as pd
from scipy.interpolate import Rbf

from Spot4DClass import Spot4D


# https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html#scipy.interpolate.Rbf
class RbfInterpolator():
    def __init__(self, trainingSamples_uWind, trainingSamples_vWind):
        self.trainingSamples_uWind = trainingSamples_uWind
        self.trainingSamples_vWind = trainingSamples_vWind
        # start training
        self.paras = {}
        with mp.Pool(processes=2) as pool: # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.pool.Pool.starmap
            self.paras['uWind'], self.paras['vWind'] = pool.starmap(Rbf, [trainingSamples_uWind, trainingSamples_vWind])
        # self.paras['uWind'] = Rbf(trainingSamples_uWind[:, 0], trainingSamples_uWind[:, 1], trainingSamples_uWind[:, 2], trainingSamples_uWind[:, 3], d=trainingSamples_uWind[:, 4], function='gaussian')
        # self.paras['vWind'] = Rbf(trainingSamples_vWind[:, 0], trainingSamples_vWind[:, 1], trainingSamples_vWind[:, 2], trainingSamples_vWind[:, 3], d=trainingSamples_vWind[:, 4], function='gaussian')


    @classmethod
    def initFromWeatherReportCaches(cls, pastWeatherReport, futureWeatherReport, longitudeLowerBound, longitudeUpperBound, latitudeLowerBound, latitudeUpperBound):
        # get training samples for uWind
        pastTrainingSamples_uWind = pastWeatherReport.getSamplesForTraining(secondsFromStart=0.0, categoryName='winds', componentName='u', longitudeLowerBound=longitudeLowerBound, longitudeUpperBound=longitudeUpperBound, latitudeLowerBound=latitudeLowerBound, latitudeUpperBound=latitudeUpperBound)
        futureTrainingSamples_uWind = futureWeatherReport.getSamplesForTraining(secondsFromStart=(futureWeatherReport.date - pastWeatherReport.date).total_seconds(), categoryName='winds', componentName='u', longitudeLowerBound=longitudeLowerBound, longitudeUpperBound=longitudeUpperBound, latitudeLowerBound=latitudeLowerBound, latitudeUpperBound=latitudeUpperBound)
        # get training samples for vWind
        pastTrainingSamples_vWind = pastWeatherReport.getSamplesForTraining(secondsFromStart=0.0, categoryName='winds', componentName='v', longitudeLowerBound=longitudeLowerBound, longitudeUpperBound=longitudeUpperBound, latitudeLowerBound=latitudeLowerBound, latitudeUpperBound=latitudeUpperBound)
        futureTrainingSamples_vWind = futureWeatherReport.getSamplesForTraining(secondsFromStart=(futureWeatherReport.date - pastWeatherReport.date).total_seconds(), categoryName='winds', componentName='v', longitudeLowerBound=longitudeLowerBound, longitudeUpperBound=longitudeUpperBound, latitudeLowerBound=latitudeLowerBound, latitudeUpperBound=latitudeUpperBound)

        return cls(
            trainingSamples_uWind=nu.concatenate([pastTrainingSamples_uWind, futureTrainingSamples_uWind]),
            trainingSamples_vWind=nu.concatenate([pastTrainingSamples_vWind, futureTrainingSamples_vWind])
        )


    def predict(self, spot, timeDelta):
        return (
            self.paras['uWind'](spot.longitude, spot.latitude, spot.altitude, timeDelta),
            self.paras['vWind'](spot.longitude, spot.latitude, spot.altitude, timeDelta)
        )
