import numpy as nu
import pandas as pd
from scipy.interpolate import griddata

from Spot4DClass import Spot4D


# https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html#scipy.interpolate.griddata
class LinearInterpolator():
    def __init__(self, trainingSamples_uWind, trainingSamples_vWind, timeStandard):
        self.trainingSamples_uWind = trainingSamples_uWind
        self.trainingSamples_vWind = trainingSamples_vWind
        self.timeStandard = timeStandard


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
            trainingSamples_vWind=nu.concatenate([pastTrainingSamples_vWind, futureTrainingSamples_vWind]),
            timeStandard=pastWeatherReport.date
        )


    def predict(self, spot):
        return (
            griddata(points=self.trainingSamples_uWind[:, :-1], values=self.trainingSamples_uWind[:, -1], xi=(spot.longitude, spot.latitude, spot.altitude, (spot.time-self.timeStandard).total_seconds()), method='linear'),
            griddata(points=self.trainingSamples_vWind[:, :-1], values=self.trainingSamples_vWind[:, -1], xi=(spot.longitude, spot.latitude, spot.altitude, (spot.time-self.timeStandard).total_seconds()), method='linear')
        )


    def predictFromSpot_flattenedArray(self, array):
        return (
            griddata(points=self.trainingSamples_uWind[:, :-1], values=self.trainingSamples_uWind[:, -1], xi=array, method='linear'),
            griddata(points=self.trainingSamples_vWind[:, :-1], values=self.trainingSamples_vWind[:, -1], xi=array, method='linear')
        )


    # longitude, latitude, altitude, time
    def predictFromSpots_ndarray(self, spotsNdarray):
        return (
            griddata(points=self.trainingSamples_uWind[:, :-1], values=self.trainingSamples_uWind[:, -1], xi=spotsNdarray, method='linear'),
            griddata(points=self.trainingSamples_vWind[:, :-1], values=self.trainingSamples_vWind[:, -1], xi=spotsNdarray, method='linear')
        )
