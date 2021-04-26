# network.searchconditions.py

from enum import Enum
from typing import Optional

import selenium.webdriver.common.by as selenium_by

import debug.logger as clog

logger = clog.getLogger(__name__)


class Strategy(Enum):
    """
    Mapper for all provided strategies searching the DOM of a web page.
    Note: The associated strings should NEVER be renamed as they get persisted by saving
    them as JSON ActionBundle files. Further these strings are referenced
    when converting dictionaries from/to Action.
    """

    IGNORE = "ignore", "Ignored"
    BY_ID = "id", "By ID"
    BY_XPATH = "xPath", "By XPath"
    BY_CLASSNAME = "classname", "By class name"
    BY_TEXT = "text", "By content text"

    def __new__(cls, value, readable: str = ""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.readable = readable
        return obj


class StrategyAdapter(selenium_by.By):

    def __init__(self, strategy: Strategy):
        self.__strategy = strategy

    def toSelenium(self) -> Optional[selenium_by.By]:
        if self.__strategy == Strategy.IGNORE:
            return None
        elif self.__strategy == Strategy.BY_TEXT:
            return self.XPATH  # this is correct as we are searching text content by XPATH
        elif self.__strategy == Strategy.BY_ID:
            return self.ID
        elif self.__strategy == Strategy.BY_XPATH:
            return self.XPATH
        elif self.__strategy == Strategy.BY_CLASSNAME:
            return self.CLASS_NAME
        else:
            raise ValueError(f"Unable to convert {self.__strategy} to selenium 'By' value.")


class SearchConditions:

    def __init__(self, strategy: Strategy = Strategy.IGNORE, identifier: str = ""):
        self.__strategy = strategy
        self.__identifier = identifier

    @property
    def searchStrategy(self) -> Strategy:
        return self.__strategy

    @property
    def identifier(self) -> str:
        return self.__identifier
