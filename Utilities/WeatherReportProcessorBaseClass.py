from enum import Enum


class WeatherReportProcessorBase():

    # class properties
    weatherReportDirNameFormat = "%Y%m%d%H%M"
    GFSWeatherReportsStorageDirPath = "/Users/yuyang/Documents/work/SimpleZeroConsumptionPlane/Utilities/RawGFSWeatherReportsStorage"
    gribFilesPath = f'{GFSWeatherReportsStorageDirPath}/gribFiles'
    csvFilesPath = f'{GFSWeatherReportsStorageDirPath}/csvFiles'
