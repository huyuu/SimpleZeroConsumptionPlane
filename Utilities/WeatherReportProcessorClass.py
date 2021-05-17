import numpy as nu
import pandas as pd
from scipy import interpolate
from sklearn import gaussian_process as gp
import sklearn as sk
import pickle
import subprocess as sp
import multiprocessing as mp
import urllib.request as urlrequest
from urllib.error import URLError
import requests
import datetime as dt
import time
import os
import shutil
import subprocess as sp
import multiprocessing as mp
from time import sleep
# self-made classes
from Spot4DClass import Spot4D
from WeatherReportRemoteProcessorClass import WeatherReportRemoteProcessor
from WeatherReportLocalProcessorClass import WeatherReportLocalProcessor


class WeatherReportProcessor():
    def __init__(self):
        # properties
        self.weatherReportRemoteProcessor = WeatherReportRemoteProcessor(currentSpot=Spot4D.initByDefaultValue())
        self.weatherReportLocalProcessor = WeatherReportLocalProcessor()
        # asyncronously download WeatherReport from remote server continuously
        self.weatherReportRemoteProcessor.asyncDownloadLatestWeatherReportFromRemoteServerContinuously()
        self.weatherReportRemoteProcessor.asyncDecodeLatestWeatherReportToCSVFilesContinuously()


    def getWeatherReportAtSpot(self, spot):
        # if weather report at certainTime can be directly calculated from curret cache
        if self.weatherReportLocalProcessor.isWeatherReportFromCurrentCacheAvailable(spot):
            return self.weatherReportLocalProcessor.getWeatherReportFromCurrentCache(spot)
        # if weather report should and can be derived from data stored at local device
        elif self.weatherReportLocalProcessor.isWeatherReportAtLocalDeviceAvailable(spot):
            self.weatherReportLocalProcessor.refreshCurrentWeathorReportCacheFromLocalDevice(spot)
            return self.weatherReportLocalProcessor.getWeatherReportFromCurrentCache(spot)
        # wait for the data from remote server
        else:
            return self.weatherReportRemoteProcessor.syncGetLatestWeatherReportFromRemoteServer(spot)



    def __translateCertainTimeToWeatherReportDatetimeFormatString(self, certainTime):
        return date


if __name__ == '__main__':
    weatherReportProcessor = WeatherReportProcessor()
    for _ in range(20):
        visibleWeatherData = weatherReportProcessor.getWeatherReportAtSpot(spot=Spot4D.initByDefaultValue())
        # visibleWeatherData.plotWinds()
        print(visibleWeatherData.df.head())
        print("")
        sleep(1)
    sleep(3600*10)
