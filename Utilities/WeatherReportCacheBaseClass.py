from enum import Enum

from WeatherReportClass import WeatherReport


class WeatherReportCacheBase(WeatherReport):
    def __init__(self, pastWeatherReport, futureWeatherReport):
        self.state = WeatherReportCacheStatus.Empty
        self.pastWeatherReport = pastWeatherReport
        self.futureWeatherReport = futureWeatherReport


class WeatherReportCacheBaseState(Enum):

    # class properties
    Valid = 1
    Invalid = 2
    Empty = 3
