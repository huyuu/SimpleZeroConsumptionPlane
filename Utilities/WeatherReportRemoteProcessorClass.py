import numpy as nu
import pandas as pd
import datetime as dt
from time import sleep
import pickle
import subprocess as sp
import multiprocessing as mp
import os
import shutil
import urllib.request as urlrequest
from urllib.error import URLError, HTTPError, ContentTooShortError
import requests
import shutil
import tempfile
import socket
import signal
from enum import Enum

from WeatherReportProcessorBaseClass import WeatherReportProcessorBase
from Spot4DClass import Spot4D

# socket.setdefaulttimeout(90)


class WeatherReportRemoteProcessor(WeatherReportProcessorBase):

    # class properties
    baseurl = "https://www.ncei.noaa.gov/data/global-forecast-system/access/grid-004-0.5-degree/forecast"
    baseurlExtension = "grb2"
    longitudeMargin = 20.0
    latitudeMargin = 20.0
    downloadTimeout = 3600


    def __init__(self, currentSpot):
        self.shouldStopListeningRemoteGFSReport = mp.Event()
        self.shouldStopListeningRemoteGFSReport.clear()

        self.didDownloadProcedureEnd = mp.Event()
        self.didDownloadProcedureEnd.set()

        self.shouldStopDecodingToCSVFiles = mp.Event()
        self.shouldStopDecodingToCSVFiles.clear()

        # create shared spot
        self.currentLongitude = mp.Value('d', float(currentSpot.longitude))
        self.currentLatitude = mp.Value('d', float(currentSpot.latitude))
        self.currentAltitude = mp.Value('d', float(currentSpot.altitude))


    # MARK: - Public Methods

    def asyncDownloadLatestWeatherReportFromRemoteServerContinuously(self):
        process = mp.Process(target=helper_asyncDownloadLatestWeatherReportFromRemoteServerContinuously, args=(self.shouldStopListeningRemoteGFSReport, self.didDownloadProcedureEnd))
        process.start()


    def asyncDecodeLatestWeatherReportToCSVFilesContinuously(self):
        process = mp.Process(target=helper_asyncDecodeLatestWeatherReportToCSVFilesContinuously, args=(self.shouldStopDecodingToCSVFiles, self.didDownloadProcedureEnd, self.currentLongitude, self.currentLatitude, self.currentAltitude))
        process.start()


    def updateCurrentSpot(self, currentSpot):
        self.currentLongitude = currentSpot.longitude
        self.currentLatitude = currentSpot.latitude
        self.currentAltitude = currentSpot.altitude


# Custom Functions from async usage

def helper_asyncDownloadLatestWeatherReportFromRemoteServerContinuously(shouldStopListeningRemoteGFSReport, didDownloadProcedureEnd):
    # final function
    def defer(didSucceed=False):
        if didSucceed:
            print(f"Retrieve end successfully. ({dt.datetime.utcnow().strftime('%Y%m%d_%H:%M')})")
        didDownloadProcedureEnd.set()
        sleep(60*10)

    # main loop
    while not shouldStopListeningRemoteGFSReport.is_set():
        didDownloadProcedureEnd.clear()
        # gribFiles folder doesn't exist
        if not os.path.isdir(f'{WeatherReportProcessorBase.gribFilesPath}'):
            os.mkdir(f'{WeatherReportProcessorBase.gribFilesPath}') # fallthrough

        # get latestTime and latest URL
        print(f"{dt.datetime.utcnow().strftime('%Y%m%d_%H:%M')}: Searching for latest release on GFS ...")
        statusCode = 0
        latestAvailableTime = dt.datetime.utcnow()
        latestAvailableTime = dt.datetime(latestAvailableTime.year, latestAvailableTime.month, latestAvailableTime.day, latestAvailableTime.hour//6*6, 0, 0)
        while statusCode != 200:
            try:
                latestURL = __getLatestURLFromTime(latestAvailableTime, precedingHours=0)
                statusCode = urlrequest.urlopen(latestURL, timeout=90).status
                if statusCode != 200:
                    raise HTTPError
            except URLError as error:
                if f"{error.reason}" == 'Not Found':
                    latestAvailableTime -= dt.timedelta(hours=6)
                # timeout
                elif f"{error.reason}" == '_ssl.c:1074: The handshake operation timed out':
                    print(f"Warning: handshake to '{latestURL}' has timed out. Retrying ...")
                else:
                    print(f"Warning: URLError has occured because: {error.reason}; Skiping ...")
                    latestAvailableTime -= dt.timedelta(hours=6)
            except HTTPError as error:
                print(f"Warning: HTTPErrorError has occured because: {error.code}, {error.reason}; Skipping ...")
                latestAvailableTime -= dt.timedelta(hours=6)
            except:
                print(f'Warning: Response with un expected error: status_code: {statusCode}; Try again after 1 minute...')
                sleep(60)

            # latestURL = __getLatestURLFromTime(latestAvailableTime)
            # response = requests.head(latestURL)
            # statusCode = response.status_code
            # if statusCode == 200:
            #     print(f"Found latest distribution of {latestAvailableTime.strftime('%Y%m%d')}_{latestAvailableTime.strftime('%H')}00. Start Download ...")
            #     break
            # elif statusCode == 404:
            #     latestAvailableTime -= dt.timedelta(hours=6)
            # else:
            #     print(f'Warning: Response with un expected error: status_code: {response.status_code}; header: {response.headers}. Try again after 1 minute...')
            #     sleep(60)

        print(f"{dt.datetime.utcnow().strftime('%Y%m%d_%H:%M')}: Found latest distribution of {latestAvailableTime.strftime('%Y%m%d')}_{latestAvailableTime.strftime('%H')}00. Start Download ...")
        del statusCode

        # if some previous downloaded data is in local storage, check if the new download is needed
        existingDirs = os.listdir(f'{WeatherReportProcessorBase.gribFilesPath}')
        existingDirs = list(filter(lambda name: 'distributed' in name, existingDirs))
        if len(existingDirs) != 0:
            existingLatestDistributionDate = []
            for name in existingDirs:
                ymdhM, _ = name.split('_')
                existingLatestDistributionDate.append(dt.datetime.strptime(ymdhM, WeatherReportProcessorBase.weatherReportDirNameFormat))
            existingLatestDistributionDate = sorted(existingLatestDistributionDate, reverse=True)
            existingLatestDistributionDate = existingLatestDistributionDate[0]
            # if latest local distribution matches the remote distribution, no download need to be conducted
            if existingLatestDistributionDate == latestAvailableTime:
                defer()
                continue

        # download latest contents
        storeDirName = f"{latestAvailableTime.strftime('%Y%m%d%H')}00_distributed"
        if os.path.isdir(f"{WeatherReportProcessorBase.gribFilesPath}/{storeDirName}"):
            shutil.rmtree(f"{WeatherReportProcessorBase.gribFilesPath}/{storeDirName}")
        os.mkdir(f"{WeatherReportProcessorBase.gribFilesPath}/{storeDirName}")
        precedingHours = 0
        while precedingHours < 385:
        # for precedingHours in nu.arange(0, 385, 3, dtype='int'):
            latestURL = __getLatestURLFromTime(latestAvailableTime, precedingHours=precedingHours)
            forecastForDate = latestAvailableTime + dt.timedelta(hours=int(precedingHours))
            storeFileName = forecastForDate.strftime("%Y%m%d%H") + "00"
            storePath = f"{WeatherReportProcessorBase.gribFilesPath}/{storeDirName}/{storeFileName}.{WeatherReportRemoteProcessor.baseurlExtension}"
            try:
                downloadLargeFileWithinTime(url=latestURL, storePath=storePath, timeout=WeatherReportRemoteProcessor.downloadTimeout)
            except mp.TimeoutError as error: # says much about error handling: https://docs.python.org/3/howto/urllib2.html#urllib-howto
                print(f"Warning: Can't download grib2 content from {latestURL} because: timeout; Retrying ...")
                if os.path.exists(storePath):
                    os.remove(storePath)
                sleep(10) # sleep for a while just in case for a bad connection is happening.
                precedingHours -= 3
            except URLError as error: # says much about error handling: https://docs.python.org/3/howto/urllib2.html#urllib-howto
                print(f"Warning: Can't download grib2 content from {latestURL} because: {error.reason}; Retrying ...")
                if os.path.exists(storePath):
                    os.remove(storePath)
                sleep(10) # sleep for a while just in case for a bad connection is happening.
                precedingHours -= 3
            except HTTPError as error: # says much about error handling: https://docs.python.org/3/howto/urllib2.html#urllib-howto
                print(f"Warning: Can't donwload grib2 content from {latestURL} with error code {error.code}, and reason: {error.reason}; Retrying ...")
                print(error.read())
                if os.path.exists(storePath):
                    os.remove(storePath)
                sleep(10)
                precedingHours -= 3
            except ContentTooShortError as error:
                print(f"Warning: Download grib2 content from {latestURL} is interrupted ; Retrying ...")
                if os.path.exists(storePath):
                    os.remove(storePath)
                sleep(10) # sleep for a while just in case for a bad connection is happening.
                precedingHours -= 3
            precedingHours += 3

        # retrieve succeed
        defer(didSucceed=True)
    return


def __getLatestURLFromTime(date, precedingHours=384):
    return f"{WeatherReportRemoteProcessor.baseurl}/{date.strftime('%Y%m')}/{date.strftime('%Y%m%d')}/gfs_4_{date.strftime('%Y%m%d_%H')}00_" + "{:03}".format(precedingHours) +f".{WeatherReportRemoteProcessor.baseurlExtension}"



def helper_asyncDecodeLatestWeatherReportToCSVFilesContinuously(shouldStopDecodingToCSVFiles, didDownloadProcedureEnd, currentLongitude, currentLatitude, currentAltitude):
    sleep(60)
    # final function
    def defer(didSucceed=False):
        if didSucceed:
            print(f"Decoding end successfully. ({dt.datetime.utcnow().strftime('%Y%m%d_%H:%M')})")
        sleep(60)
    # main loop
    while not shouldStopDecodingToCSVFiles.is_set():
        # wait until download procedure end
        didDownloadProcedureEnd.wait()

        print("start decoding ...")
        # get latest downloaded grib files
        latestDownloadedDistribution = list(filter(lambda name: 'distributed' in name, os.listdir(f'{WeatherReportProcessorBase.gribFilesPath}')))
        if len(latestDownloadedDistribution) == 0: # if no downloaded data, skip
            continue
        latestDownloadedDistribution = sorted([ dt.datetime.strptime(name.split('_')[0], '%Y%m%d%H%M') for name in latestDownloadedDistribution ], reverse=True)[0]
        # get latest stored distribution
        latestStoredDistribution = list(filter(lambda name: 'distributed' in name, os.listdir(f'{WeatherReportProcessorBase.csvFilesPath}')))
        if len(latestStoredDistribution) == 0:
            latestStoredDistribution = None
        else:
            latestStoredDistribution = sorted([ dt.datetime.strptime(name.split('00_d')[0], '%Y%m%d%H') for name in latestStoredDistribution ], reverse=True)[0]
        # if they match each other, do nothing
        if latestStoredDistribution == latestDownloadedDistribution:
            defer(didSucceed=False)
            continue

        # start main process: decode all grib in the latest distribution dir

        # first, get boundaries
        longitudeLowerBound = currentLongitude.value - WeatherReportRemoteProcessor.longitudeMargin
        longitudeUpperBound = currentLongitude.value + WeatherReportRemoteProcessor.longitudeMargin
        latitudeLowerBound = currentLatitude.value - WeatherReportRemoteProcessor.latitudeMargin
        latitudeUpperBound = currentLatitude.value + WeatherReportRemoteProcessor.latitudeMargin
        distributionName = f"{latestDownloadedDistribution.strftime('%Y%m%d%H')}00_distributed"

        # second, if the specific distribution dir in csvFiles dowsn't exist, make a new one. Otherwise remove it.
        if os.path.isdir(f"{WeatherReportProcessorBase.csvFilesPath}/{distributionName}"):
            shutil.rmtree(f"{WeatherReportProcessorBase.csvFilesPath}/{distributionName}")
        os.mkdir(f"{WeatherReportProcessorBase.csvFilesPath}/{distributionName}")

        # main decoding
        for gribFileName in filter(lambda name: '.grb2' in name, os.listdir(f"{WeatherReportProcessorBase.gribFilesPath}/{distributionName}")):
            # get grib file path
            gribFilePath = f'{WeatherReportProcessorBase.gribFilesPath}/{distributionName}/{gribFileName}'
            # get csv file path
            csvParametersDirName = gribFileName.split('.')[0]
            csvParametersDirPath = f'{WeatherReportProcessorBase.csvFilesPath}/{distributionName}/{csvParametersDirName}'
            os.mkdir(csvParametersDirPath)
            # ready! call subprocess script
            sp.run(['./decodeGribToCSVFiles.sh', f"{gribFilePath}", f"{csvParametersDirPath}", f'{latitudeLowerBound}', f'{latitudeUpperBound}', f'{longitudeLowerBound}', f'{longitudeUpperBound}'])

        # finally
        defer(didSucceed=True)
    return


# https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Process.exitcode
# http://ja.pymotw.com/2/multiprocessing/basics.html
def downloadLargeFileWithinTime(url, storePath, timeout):
    # async way to do: urlrequest.urlretrieve(url=latestURL, filename=storePath)
    downloadProcess = mp.Process(target=urlrequest.urlretrieve, args=(url, storePath))
    downloadProcess.start()

    # when timeout reaches, the method will return None. One should manully terminate the process then.
    if downloadProcess.join(timeout) is None:
        downloadProcess.terminate()
        sleep(1)

    if downloadProcess.exitcode == -signal.SIGTERM:
        raise mp.TimeoutError
    else:
        return

    # # another option1:
    # # https://docs.python.org/3/howto/urllib2.html#urllib-howto
    # # https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3
    # with urlrequest.urlopen(latestURL, timeout=20) as response, open(storePath, 'wb') as file:
    #     shutil.copyfileobj(response, file)


    # # another option2:
    # # https://stackoverflow.com/questions/32763720/timeout-a-file-download-with-python-urllib
    # # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    # request = requests.get(latestURL, stream=True)
    # _startTime = dt.datetime.utcnow()
    # with open(storePath, 'wb') as file:
    #     for chunk in request.iter_content(1024*128):
    #         file.write(chunk)
    #         if (dt.datetime.utcnow() - _startTime).total_seconds() > WeatherReportRemoteProcessor.downloadTimeout:
    #             raise mp.TimeourError
