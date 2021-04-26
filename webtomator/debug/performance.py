# performance.py

import time
from abc import ABC, abstractmethod


class IPerformance(ABC):

    @abstractmethod
    def setTimeMarker(self):
        pass

    @abstractmethod
    def getInfo(self) -> str:
        pass

    @abstractmethod
    def overallTimeStr(self) -> str:
        pass


class Performance(IPerformance):

    def __init__(self):
        self.__t = 0
        self.__overallTime = 0

    def setTimeMarker(self):
        self.__t = time.time()

    def getInfo(self) -> str:
        elapsed = round(time.time() - self.__t, 2)
        self.__sumPerformance(elapsed)
        return str(elapsed) + " seconds"

    @property
    def overallTimeStr(self):
        return str(round(self.__overallTime, 2))

    def __sumPerformance(self, seconds):
        self.__overallTime += seconds
