import numpy as nu
import pandas as pd
import datetime as dt
import os
import urllib.request as urlrequest
from urllib.error import URLError
from enum import Enum
import multiprocessing as mp
# self-made classes
from Spot4DClass import Spot4D
from WeatherReportProcessorBaseClass import WeatherReportProcessorBase
from WeatherReportClass import WeatherReport
from WeatherReportRemoteProcessorClass import WeatherReportRemoteProcessor
from LinearInterpolatorClass import LinearInterpolator
from GaussianProcessRegressorInterpolatorClass import GaussianProcessRegressorInterpolator
from RbfInterpolatorClass import RbfInterpolator
from VisibleWeatherDataClass import VisibleWeatherData


class WeatherReportCacheState(Enum):
    # class properties
    Valid = 1
    Invalid = 2
    Empty = 3


class WeatherReportLocalProcessor(WeatherReportProcessorBase):

    # class properties
    longitudeMargin = 5.0
    latitudeMargin = 5.0


    def __init__(self):
        # properties
        # weather report caches
        self.weatherReportCaches = {
            'pastWeatherReport': None,
            'futureWeatherReport': None,
            'predictionModels': {},
            'state': WeatherReportCacheState.Empty
        }


    def isWeatherReportFromCurrentCacheAvailable(self, spot):
        # if invalid, return False
        if self.weatherReportCaches['state'] != WeatherReportCacheState.Valid or self.weatherReportCaches['pastWeatherReport'] is None or self.weatherReportCaches['futureWeatherReport'] is None or self.weatherReportCaches['predictionModels'] is {}:
            return False
        # if valid last time, check if spot is inside the boundary
        # timeBefore, timeAfter = spot.getTimeBounds()
        pastBoundarySpots = self.weatherReportCaches['pastWeatherReport'].get8WideBoundarySpots()
        futureBoundarySpots = self.weatherReportCaches['futureWeatherReport'].get8WideBoundarySpots()
        # if caches can be used for certainTime, return yes.
        if self.weatherReportCaches['state'] == WeatherReportCacheState.Valid and spot.isInside(pastBoundarySpots + futureBoundarySpots):
            return True
        # else, return no.
        else:
            # set caches to neededRefresh state
            self.weatherReportCaches['state'] = WeatherReportCacheState.Invalid
            return False


    # heavy calculation done on main thread.
    def getWeatherReportFromCurrentCache(self, spot):
        return VisibleWeatherData(
            interpolator=self.weatherReportCaches['predictionModels']['Linear'],
            centerSpot=spot
        )
        # return self.weatherReportCaches['predictionModels']['Linear'].predict(spot)



    def isWeatherReportAtLocalDeviceAvailable(self, spot):
        timeBefore, timeAfter = spot.getTimeBounds()
        try:
            _ = WeatherReport.findBestParametersDirPathForTime(timeBefore)
            _ = WeatherReport.findBestParametersDirPathForTime(timeAfter)
        except FileNotFoundError as error: # https://docs.python.org/ja/3/library/exceptions.html
            print(f"{timeBefore} or {timeAfter} is covered by none of the distribution.")
            return False
        return True


    def refreshCurrentWeathorReportCacheFromLocalDevice(self, spot):
        timeBefore, timeAfter = spot.getTimeBounds()
        # refresh pastReport
        pastSpot = Spot4D.initFromCopy(spot)
        pastSpot.time = timeBefore
        self.weatherReportCaches['pastWeatherReport'] = WeatherReport.initFromCenterSpotAtFixTime(spot=pastSpot)
        # refresh future report
        futureSpot = Spot4D.initFromCopy(spot)
        futureSpot.time = timeAfter
        self.weatherReportCaches['futureWeatherReport'] = WeatherReport.initFromCenterSpotAtFixTime(spot=futureSpot)

        # refresh model
        # boundaries needed
        longitudeLowerBound, longitudeUpperBound, latitudeLowerBound, latitudeUpperBound, _, _ = spot.getSurroundingLongitudeLatitudeAltitudeBoundary(longitudeMargin=WeatherReportLocalProcessor.longitudeMargin, latitudeMargin=WeatherReportLocalProcessor.latitudeMargin)

        # init prediction models
        self.weatherReportCaches['predictionModels']['Linear'] = LinearInterpolator.initFromWeatherReportCaches(
            pastWeatherReport=self.weatherReportCaches['pastWeatherReport'],
            futureWeatherReport=self.weatherReportCaches['futureWeatherReport'],
            longitudeLowerBound = longitudeLowerBound,
            longitudeUpperBound = longitudeUpperBound,
            latitudeLowerBound = latitudeLowerBound,
            latitudeUpperBound = latitudeUpperBound
        )
        # self.weatherReportCaches['predictionModels']['GaussianProcessRegressor'] = GaussianProcessRegressorInterpolator.initFromWeatherReportCaches(
        #     pastWeatherReport=self.weatherReportCaches['pastWeatherReport'],
        #     futureWeatherReport=self.weatherReportCaches['futureWeatherReport'],
        #     longitudeLowerBound = longitudeLowerBound,
        #     longitudeUpperBound = longitudeUpperBound,
        #     latitudeLowerBound = latitudeLowerBound,
        #     latitudeUpperBound = latitudeUpperBound
        # )

        # refresh state
        self.weatherReportCaches['state'] = WeatherReportCacheState.Valid
