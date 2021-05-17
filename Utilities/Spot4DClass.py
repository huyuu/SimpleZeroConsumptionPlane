import numpy as nu
import datetime as dt

from WeatherReportProcessorBaseClass import WeatherReportProcessorBase


class Spot4D():
    def __init__(self, time, longitude, latitude, altitude):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.time = time
        self.timeCurrentDirName = time.strftime(WeatherReportProcessorBase.weatherReportDirNameFormat)
        # vars for Box Calculation
        self.__timeBefore = None
        self.__timeBeforeDirName = None
        self.__timeAfter = None
        self.__timeAfterDirName = None

        self.latitudeBefore = None
        self.latitudeAfter = None

        self.longitudeBefore = None
        self.longitudeAfter = None

        self.altitudeBefore = None
        self.altitudeAfter = None


    @classmethod
    def initFromCopy(cls, spot):
        return cls(spot.time, spot.longitude, spot.latitude, spot.altitude)


    @classmethod
    def initByDefaultValue(cls): # only for debug usage
        time = dt.datetime.utcnow()
        longitude = 35.4808174
        latitude = 139.59999
        altitude = 50.0
        return cls(time, longitude, latitude, altitude)


    # MARK: - Public Methods

    def getTimeBounds(self):
        if self.__timeBefore is None or self.__timeAfter is None:
            self.__initVarsForBoxCalculation()
        return self.__timeBefore, self.__timeAfter


    def getTimeBoundsDirNames(self):
        if self.__timeBeforeDirName is None or self.__timeAfterDirName is None:
            self.__initVarsForBoxCalculation()
        return self.__timeBeforeDirName, self.__timeAfterDirName


    def get16SurroundingBoxSpots(self):
        pass


    def isInside(self, boundarySpots):
        return not self.isOutside(boundarySpots)


    def isOutside(self, boundarySpots):
        vertexes4DIndex = Spot4D.__get4DArrayOfBoundaryBoxVertexesIndex(boundarySpots)
        # check time
        for lowerTimeVertexIndex in vertexes4DIndex[0, :, :, :].flatten():
            lowerTimeVertex = boundarySpots[lowerTimeVertexIndex]
            if self.time < lowerTimeVertex.time:
                return True
        for upperTimeVertexIndex in vertexes4DIndex[1, :, :, :].flatten():
            upperTimeVertex = boundarySpots[upperTimeVertexIndex]
            if self.time > upperTimeVertex.time:
                return True
        # check longitude
        for lowerLongitudeVertexIndex in vertexes4DIndex[:, 0, :, :].flatten():
            lowerLongitudeVertex = boundarySpots[lowerLongitudeVertexIndex]
            if self.longitude < lowerLongitudeVertex.longitude:
                return True
        for upperLongitudeVertexIndex in vertexes4DIndex[:, 1, :, :].flatten():
            upperLongitudeVertex = boundarySpots[upperLongitudeVertexIndex]
            if self.longitude > upperLongitudeVertex.longitude:
                return True
        # check latitude
        for lowerLatitudeVertexIndex in vertexes4DIndex[:, :, 0, :].flatten():
            lowerLatitudeVertex = boundarySpots[lowerLatitudeVertexIndex]
            if self.latitude < lowerLatitudeVertex.latitude:
                return True
        for upperLatitudeVertexIndex in vertexes4DIndex[:, :, 1, :].flatten():
            upperLatitudeVertex = boundarySpots[upperLatitudeVertexIndex]
            if self.latitude > upperLatitudeVertex.latitude:
                return True
        # check altitude
        for lowerAltitudeVertexIndex in vertexes4DIndex[:, :, :, 0].flatten():
            lowerAltitudeVertex = boundarySpots[lowerAltitudeVertexIndex]
            if self.altitude < lowerAltitudeVertex.altitude:
                return True
        for upperAltitudeVertexIndex in vertexes4DIndex[:, :, :, 1].flatten():
            upperAltitudeVertex = boundarySpots[upperAltitudeVertexIndex]
            if self.altitude > upperAltitudeVertex.altitude:
                return True
        # else
        return False


    def getSurroundingLongitudeLatitudeAltitudeBoundary(self, longitudeMargin, latitudeMargin):
        return (
            self.longitude - longitudeMargin,
            self.longitude + longitudeMargin,
            self.latitude - latitudeMargin,
            self.latitude + latitudeMargin,
            10, # altitude lower bound
            100 # altitude upper bound
        )



    # MARK: - Special Methods

    def __eq__(self, other):
        return self.time == other.time and self.longitude == other.longitude and self.laitude == other.latitude and self.altitude == other.altitude


    def __lt__(self, other): # time > longitude > latitude > altitude
        if self.time != other.time:
            return self.time < other.time
        elif self.longitude != other.longitude:
            return self.longitude < other.longitude
        elif self.latitude != other.latitude:
            return self.latitude < other.latitude
        else:
            return self.altitude < other.altitude


    # MARK: - Helper Custom Private methods

    def __initVarsForBoxCalculation(self):
        # get the former and following time points between which the certainTime lies.
        self.__timeBefore = dt.datetime(self.time.year, self.time.month, self.time.day, self.time.hour//3*3, 0, 0)
        self.__timeBeforeDirName = self.__timeBefore.strftime(WeatherReportProcessorBase.weatherReportDirNameFormat)
        self.__timeAfter = self.__timeBefore + dt.timedelta(hours=3)
        self.__timeAfterDirName = self.__timeAfter.strftime(WeatherReportProcessorBase.weatherReportDirNameFormat)
        #


    # MARK: - Helper Custom Private Classmethods

    @classmethod
    def __get4DArrayOfBoundaryBoxVertexesIndex(cls, boundarySpots):
        boundarySpots.sort() # time > longitude > latitude > altitude
        vertexesIndex = nu.zeros((2, 2, 2, 2), dtype='int')
        # dump 1DboundarySpots into 4DvertexesArray
        count = 0
        for i in (0, 1):
            for j in (0, 1):
                for k in (0, 1):
                    for u in (0, 1):
                        vertexesIndex[i, j, k, u] = count
                        count += 1
        return vertexesIndex


    @classmethod
    def __get3DArrayOfBoundaryBoxVertexesIndex(cls, boundarySpots):
        boundarySpots.sort()
        vertexesIndex = nu.zeros((2, 2, 2), dtype='int')
        # dump 1DboundarySpots into 4DvertexesArray
        count = 0
        for i in (0, 1):
            for j in (0, 1):
                for k in (0, 1):
                        vertexesIndex[i, j, k] = count
                        count += 1
        return vertexesIndex
