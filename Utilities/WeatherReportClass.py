import numpy as nu
import pandas as pd
import datetime as dt
from time import sleep
import os
from copy import deepcopy

from WeatherReportProcessorBaseClass import WeatherReportProcessorBase
from WeatherReportRemoteProcessorClass import WeatherReportRemoteProcessor
from Spot4DClass import Spot4D


class WeatherReport():

    # class properties
    windSpeedAltitudeBaseGradation = ['10_m', '20_m', '30_m', '40_m', '50_m', '80_m', '100_m']
    geoCoordinateEpsilon = 1e-6


    # All-term initializer. Only for private access.
    def __init__(self,
        date,
        latitudeUpperBound,
        latitudeLowerBound,
        longitudeUpperBound,
        longitudeLowerBound,
        _10mHighWindSpeed_vWind,
        _10mHighWindSpeed_uWind,
        _20mHighWindSpeed_vWind,
        _20mHighWindSpeed_uWind,
        _30mHighWindSpeed_vWind,
        _30mHighWindSpeed_uWind,
        _40mHighWindSpeed_vWind,
        _40mHighWindSpeed_uWind,
        _50mHighWindSpeed_vWind,
        _50mHighWindSpeed_uWind,
        _80mHighWindSpeed_vWind,
        _80mHighWindSpeed_uWind,
        _100mHighWindSpeed_vWind,
        _100mHighWindSpeed_uWind
    ):
        # properties
        # basic
        self.date = date
        self.latitudeLowerBound = latitudeLowerBound
        self.latitudeUpperBound = latitudeUpperBound
        self.longitudeLowerBound = longitudeLowerBound
        self.longitudeUpperBound = longitudeUpperBound
        self.altitudeLowerBound = 10 # meter
        self.altitudeUpperBound = 100 # meter
        # value
        self.value = {
            'winds': {
                '10_m': {
                    'u': _10mHighWindSpeed_uWind,
                    'v': _10mHighWindSpeed_vWind,
                },
                '20_m': {
                    'u': _20mHighWindSpeed_uWind,
                    'v': _20mHighWindSpeed_vWind,
                },
                '30_m': {
                    'u': _30mHighWindSpeed_uWind,
                    'v': _30mHighWindSpeed_vWind,
                },
                '40_m': {
                    'u': _40mHighWindSpeed_uWind,
                    'v': _40mHighWindSpeed_vWind,
                },
                '50_m': {
                    'u': _50mHighWindSpeed_uWind,
                    'v': _50mHighWindSpeed_vWind,
                },
                '80_m': {
                    'u': _80mHighWindSpeed_uWind,
                    'v': _80mHighWindSpeed_vWind,
                },
                '100_m': {
                    'u': _100mHighWindSpeed_uWind,
                    'v': _100mHighWindSpeed_vWind,
                },
            },
        }


    @classmethod
    def initFromCenterSpotAtFixTime(cls, spot):
        # set
        # longitudeLowerBound = spot.longitude - WeatherReportRemoteProcessor.longitudeMargin
        # longitudeUpperBound = spot.longitude + WeatherReportRemoteProcessor.longitudeMargin
        # latitudeLowerBound = spot.latitude - WeatherReportRemoteProcessor.latitudeMargin
        # latitudeUpperBound = spot.latitude + WeatherReportRemoteProcessor.latitudeMargin
        longitudeLowerBound = 90
        longitudeUpperBound = -90
        latitudeLowerBound = 180
        latitudeUpperBound = -180
        # find latest parametersDirPath
        parametersDirPath = WeatherReport.findBestParametersDirPathForTime(spot.time)
        # dump args
        args = []
        for levelName in WeatherReport.windSpeedAltitudeBaseGradation:
            # get u component wind data frame
            uWindDF = pd.read_csv(f'{parametersDirPath}/{levelName}_uWind.csv', header=None)
            uWindDF.columns = ['latitude', 'longitude', 'value']
            # find boundaries
            uLongitudeLowerBound = uWindDF['longitude'].min()
            uLongitudeUpperBound = uWindDF['longitude'].max()
            uLatitudeLowerBound = uWindDF['latitude'].min()
            uLatitudeUpperBound = uWindDF['latitude'].max()
            # dump to pivot table
            # uWindDF = uWindDF.pivot('longitude', 'latitude', values='value')
            args.append(uWindDF) # append uWind

            # get v component wind data frame
            vWindDF = pd.read_csv(f'{parametersDirPath}/{levelName}_vWind.csv', header=None)
            vWindDF.columns = ['latitude', 'longitude', 'value']
            # find boundaries
            vLongitudeLowerBound = vWindDF['longitude'].min()
            vLongitudeUpperBound = vWindDF['longitude'].max()
            vLatitudeLowerBound = vWindDF['latitude'].min()
            vLatitudeUpperBound = vWindDF['latitude'].max()
            # dump to pivot table
            # vWindDF = vWindDF.pivot('longitude', 'latitude', values='value')
            args.append(vWindDF) # append vWind

            # ensure all boundaries match each other
            # longitude lower bound
            if abs(uLongitudeLowerBound - vLongitudeLowerBound) > WeatherReport.geoCoordinateEpsilon:
                print("Warning: uWind longitude lower bound (={:.6f}) dismatch vWind longitude lower bound (={:.6f}).".format(uLongitudeLowerBound, vLongitudeLowerBound))
            else: # u & v boundary match
                longitudeLowerBound = min(longitudeLowerBound, uLongitudeLowerBound)
            # latitude lower boun
            if abs(uLatitudeLowerBound - vLatitudeLowerBound) > WeatherReport.geoCoordinateEpsilon:
                print("Warning: uWind latitude lower bound (={:.6f}) dismatch vWind latitude lower bound (={:.6f}).".format(uLatitudeLowerBound, vLatitudeLowerBound))
            else: # u & v boundary match
                latitudeLowerBound = min(latitudeLowerBound, uLatitudeLowerBound)
            # longitude upper bound
            if abs(uLongitudeUpperBound - vLongitudeUpperBound) > WeatherReport.geoCoordinateEpsilon:
                print("Warning: uWind longitude upper bound (={:.6f}) dismatch vWind longitude upper bound (={:.6f}).".format(uLongitudeUpperBound, vLongitudeUpperBound))
            else: # u & v boundary match
                longitudeUpperBound = max(longitudeUpperBound, uLongitudeUpperBound)
            # latitude upper boun
            if abs(uLatitudeUpperBound - vLatitudeUpperBound) > WeatherReport.geoCoordinateEpsilon:
                print("Warning: uWind latitude upper bound (={:.6f}) dismatch vWind latitude upper bound (={:.6f}).".format(uLatitudeUpperBound, vLatitudeUpperBound))
            else: # u & v boundary match
                latitudeUpperBound = max(latitudeUpperBound, uLatitudeUpperBound)

        return cls(spot.time, latitudeUpperBound, latitudeLowerBound, longitudeUpperBound, longitudeLowerBound, *args)


    # MARK: - Custom Public Helper Functions

    # return the 8 boundary vertex spots
    def get8WideBoundarySpots(self):
        return [
            Spot4D(self.date, self.longitudeLowerBound, self.latitudeLowerBound, self.altitudeLowerBound),
            Spot4D(self.date, self.longitudeLowerBound, self.latitudeLowerBound, self.altitudeUpperBound),
            Spot4D(self.date, self.longitudeLowerBound, self.latitudeUpperBound, self.altitudeLowerBound),
            Spot4D(self.date, self.longitudeLowerBound, self.latitudeUpperBound, self.altitudeUpperBound),
            Spot4D(self.date, self.longitudeUpperBound, self.latitudeLowerBound, self.altitudeLowerBound),
            Spot4D(self.date, self.longitudeUpperBound, self.latitudeLowerBound, self.altitudeUpperBound),
            Spot4D(self.date, self.longitudeUpperBound, self.latitudeUpperBound, self.altitudeLowerBound),
            Spot4D(self.date, self.longitudeUpperBound, self.latitudeUpperBound, self.altitudeUpperBound)
        ]


    def getSamplesForTraining(self, secondsFromStart, categoryName, componentName, longitudeLowerBound, longitudeUpperBound, latitudeLowerBound, latitudeUpperBound):
        trainingSamples = nu.zeros((1, 5)) # longitudes, latitudes, altitudes, time, value
        for level in WeatherReport.windSpeedAltitudeBaseGradation:
            altitude = float(level.split('_')[0])
            df = self.value[categoryName][level][componentName]
            # only samples in boundary should be used to train
            df = df.loc[longitudeLowerBound <= df['longitude'], :]
            df = df.loc[df['longitude'] <= longitudeUpperBound, :]
            df = df.loc[latitudeLowerBound <= df['latitude'], :]
            df = df.loc[df['latitude'] <= latitudeUpperBound, :]
            df['altitude'] = altitude
            df['time'] = secondsFromStart
            trainingSamples = nu.concatenate([trainingSamples, df[['longitude', 'latitude', 'altitude', 'time', 'value']].values])
        # delete the first row
        trainingSamples = nu.delete(trainingSamples, obj=0, axis=0)
        # print(trainingSamples)
        return trainingSamples


    # MARK: - Custom Private Helper Functions

    @classmethod
    def findBestParametersDirPathForTime(cls, _time):
        # round time
        time = deepcopy(_time)
        time = dt.datetime(time.year, time.month, time.day, time.hour//3*3, 0, 0)
        # in case csvFilesPath doesn't exist
        if not os.path.isdir(f'{WeatherReportProcessorBase.csvFilesPath}'):
            raise FileNotFoundError
        # get existing distributions
        existingDistributions = os.listdir(f'{WeatherReportProcessorBase.csvFilesPath}')
        existingDistributions = list(filter(lambda name: 'distributed' in name, existingDistributions))
        if len(existingDistributions) == 0:
            raise FileNotFoundError
        existingDistributions = sorted([ dt.datetime.strptime(dirName.split('_')[0], WeatherReportProcessorBase.weatherReportDirNameFormat) for dirName in existingDistributions ], reverse=True)
        # get the one distribution which contains the specific time
        bestDistributionDirName = None
        specificParametersDirName = time.strftime(WeatherReportProcessorBase.weatherReportDirNameFormat)
        for distributionDate in existingDistributions:
            distributionName = distributionDate.strftime(WeatherReportProcessorBase.weatherReportDirNameFormat) + '_distributed'
            if specificParametersDirName in os.listdir(f"{WeatherReportProcessorBase.csvFilesPath}/{distributionName}"):
                bestDistributionDirName = distributionName
                break
        # if none of the distributions contain the specific time, raise NotFo
        if bestDistributionDirName is None:
            raise FileNotFoundError
        else:
            return f"{WeatherReportProcessorBase.csvFilesPath}/{bestDistributionDirName}/{specificParametersDirName}"
