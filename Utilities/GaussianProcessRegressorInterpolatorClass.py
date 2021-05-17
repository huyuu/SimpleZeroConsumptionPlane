import numpy as nu
import pandas as pd
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

from Spot4DClass import Spot4D


# https://scikit-learn.org/stable/auto_examples/gaussian_process/plot_gpr_co2.html
class GaussianProcessRegressorInterpolator():
    def __init__(self, trainingSamples_uWind, trainingSamples_vWind):
        self.models = {}
        # get kernel
        _kernel1 = 66.0**2 * RBF()
        self.models['uWind'] = GaussianProcessRegressor(kernel=_kernel1)
        self.models['vWind'] = GaussianProcessRegressor(kernel=_kernel1)
        # start training
        self.models['uWind'].fit(trainingSamples_uWind[:, :-1], trainingSamples_uWind[:, -1])
        self.models['vWind'].fit(trainingSamples_vWind[:, :-1], trainingSamples_vWind[:, -1])


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
            self.models['uWind'].predict(spot.longitude, spot.latitude, spot.altitude, timeDelta),
            self.models['vWind'].predict(spot.longitude, spot.latitude, spot.altitude, timeDelta)
        )
