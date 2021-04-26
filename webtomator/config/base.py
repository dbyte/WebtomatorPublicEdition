# config.base.py
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, overload

import tinydb as tdb

import debug.logger as clog
from storage.tinyDao import TinyDao

if TYPE_CHECKING:
    from typing import ClassVar, Union
    from storage.base import Dao

logger = clog.getLogger(__name__)

# This is needed to find the 'userdata' resources folder when running
# the app from a pyinstaller build. The location of 'userdata' was then specified with the .spec
# file which is located beside the script that starts this app.
# noqa See https://hackernoon.com/the-one-stop-guide-to-easy-cross-platform-python-freezing-part-1-c53e66556a0a
isAppFrozen = getattr(sys, "frozen", False)
frozenTempPath = getattr(sys, '_MEIPASS', '')

APP_USERDATA_DIR = None

if isAppFrozen:
    APP_USERDATA_DIR = Path(frozenTempPath, "userdata")

else:
    APP_USERDATA_DIR = Path(__file__).parent / "../../userdata"


@dataclass
class LoggerConfig:
    """ Data wrapper for logging configuration repo.
    Be warned: Attribute names must exactly correspond to key names in JSON data! """
    isConsoleLogging: bool
    isFileLogging: bool
    consoleLogLevel: int
    fileLogLevel: int


@dataclass
class ScraperConfig:
    """ Data wrapper for scraper configuration repo.
    Be warned: Attribute names must exactly correspond to key names in JSON data! """
    iterSleepFromScnds: int
    iterSleepToScnds: int
    iterSleepSteps: float
    fetchTimeoutScnds: int
    fetchMaxRetries: int
    fetchUseRandomProxy: bool
    postTimeoutScnds: int
    postMaxRetries: int
    postUseRandomProxies: bool


class TinyConfigDao(TinyDao):
    _TABLE_NAME: ClassVar[str] = "Config"
    _DEFAULT_PATH: ClassVar = APP_USERDATA_DIR / "Config.json"

    def __init__(self, path: Path = None):
        path = path or self._DEFAULT_PATH
        super().__init__(path=path, table=self._TABLE_NAME)

    @overload
    def find(self, loggerConfig) -> LoggerConfig:
        ...

    @overload
    def find(self, scraperCommonConfig) -> ScraperConfig:
        ...

    @overload
    def find(self, scraperConfigByUrl: str) -> ScraperConfig:
        ...

    def find(self, **kwargs) -> Union[LoggerConfig, ScraperConfig]:
        """ Find one ore more application configurations, depending on given args.

        :param kwargs:
            'loggerConfig': Find config for the app's logging behaviour.
            'scraperCommonConfig': Find the common config, for example used as a fallback.
            'scraperConfigByUrl': Find a specific scraper config by its scraper-URL.
        :return: Results depend on which find arguments where used to call this method.
        :raises: When no or multiple configuration data were found.
        """
        if "loggerConfig" in kwargs:
            return self._findLoggerConfig()

        if "scraperCommonConfig" in kwargs:
            return self._findScraperCommonConfig()  # raises

        if "scraperConfigByUrl" in kwargs:
            return self._findScraperConfigByUrl(kwargs["scraperConfigByUrl"])  # raises

        else:
            raise KeyError(f"Configuration search fail. None of the expected arguments were given. "
                           f"kwargs: {kwargs}")

    def _findLoggerConfig(self) -> LoggerConfig:
        """ Searches the logger configuration. Falls back to a hard coded rescue
        configuration if persistent default does not exist. Returns gracefully.

        :return: A LoggerConfig object
        """
        loggerQuery = tdb.Query().logger
        try:
            results = super().find(condition=loggerQuery)  # raises
            if not results: raise LookupError("No results for query %s", loggerQuery)

        except Exception as e:
            rescueConfig = LoggerConfig(
                isConsoleLogging=True,
                isFileLogging=False,
                consoleLogLevel=clog.INFO,
                fileLogLevel=clog.NOTSET)

            logger.warning(
                "Did not find logger configuration in storage %s. Falling back to rescue "
                "configuration. Error was: %s. Recover to rescue values: %s",
                self.connection.path, e, rescueConfig)

            return rescueConfig

        else:
            # Note: Let possible exceptions raise ungracefully here.
            config = results[0]["logger"]
            decodedConfig = LoggerConfig(**config)
            return decodedConfig

    def _findScraperConfigByUrl(self, url: str) -> ScraperConfig:
        """ Searches a scraper config (inside the 'Config' table) with the given scraper URL.
        If the config does not exist, we try to fall back to a persistent default configuration.

        :param url: A scraper's URL to search for
        :return: A ScraperConfig object
        :raises: When URL was not found, or multiple URLs were found
        """
        allScrapersByUrl = tdb.Query().scraperByUrl.any(url)

        try:
            results = super().find(condition=allScrapersByUrl)  # raises
            self._raiseOnInvalidScraperResults(results=results, query=allScrapersByUrl)

        except Exception as e:
            # Concrete configuration not found, fallback to defaults.
            logger.warning(
                "Did not find scraper configuration for URL %s, falling back to default "
                "configuration in storage %s. Error was: %s", url, self.connection.path, e)

            results = self._findScraperCommonConfig()
            return results

        else:
            # Note: Let possible exceptions raise ungracefully here.
            config = results[0]["scraperByUrl"][url]
            decodedConfig = ScraperConfig(**config)
            logger.debug("Loaded scraper configuration for %s", url)
            return decodedConfig

    def _findScraperCommonConfig(self) -> ScraperConfig:
        """ Get persistent default scraper configuration. Falls back to a hard coded
        rescue configuration if persistent default does not exist.

        :return: A ScraperConfig object
        """
        commonScraperQuery = tdb.Query().scraperCommon

        try:
            results = super().find(condition=commonScraperQuery)  # raises
            self._raiseOnInvalidScraperResults(results=results, query=commonScraperQuery)

        except Exception as e:
            # No repo record found at all. Configure a default object manually for the rescue.
            rescueConfig = ScraperConfig(
                iterSleepFromScnds=20,
                iterSleepToScnds=30,
                iterSleepSteps=0.5,
                fetchTimeoutScnds=8,
                fetchMaxRetries=4,
                fetchUseRandomProxy=True,
                postTimeoutScnds=8,
                postMaxRetries=4,
                postUseRandomProxies=True)

            logger.warning("No default configuration for scrapers found at %s. Error was: %s "
                           "Falling back to rescue-configuration: %s",
                           self.connection.path, e, rescueConfig)

            return rescueConfig

        else:
            # Note: Let possible exceptions raise ungracefully here.
            config = results[0]["scraperCommon"]
            decodedConfig = ScraperConfig(**config)
            logger.debug("Loaded default scraper configuration.")
            return decodedConfig

    @staticmethod
    def _raiseOnInvalidScraperResults(results, query) -> None:
        if not results:
            raise LookupError(f"Scraper configuration was not found for query {query}.")

        if isinstance(results, list):
            foundCount = len(results)

            if foundCount == 1:
                # Valid result, just return to core method
                return

            elif foundCount == 0:
                raise LookupError(f"No valid scraper configuration found for query {query}.")

            elif foundCount > 1:
                raise LookupError(
                    f"Scraper configuration search failed for query {query}. "
                    f"Found multiple scraper configs: {results}")


class ConfigRepo:

    def __init__(self, dao: Dao):
        self._dao = dao

    def findLoggerConfig(self) -> LoggerConfig:
        """ Searches the logger configuration. Falls back to a hard coded rescue
        configuration if record does not exist. Returns gracefully.

        :return: A LoggerConfig object
        """
        with self._dao as dao:
            loggerConfig = dao.find(loggerConfig=True)
        return loggerConfig

    def findScraperConfigByUrl(self, url: str) -> ScraperConfig:
        """ Searches a scraper config (inside the 'Config' table) with the given scraper URL.
        If the config does not exist, we try to fall back to a persistent default configuration.

        :param url: A scraper's URL to search for
        :return: A ScraperConfig object
        """
        with self._dao as dao:
            scraperConfig = dao.find(scraperConfigByUrl=url)  # raises
        return scraperConfig

    def findScraperCommonConfig(self) -> ScraperConfig:
        """ Get persistent default scraper configuration. Falls back to a hard coded rescue
        configuration if persistent default does not exist.

        :return: A ScraperConfig object
        """
        with self._dao as dao:
            scraperConfig = dao.find(scraperCommonConfig=True)  # raises
        return scraperConfig


# Globals --------------------------------------------------------------------------------

# Setup global reference for application configuration repository.
# This should only be executed once - except for tests, where we may override these values.
APP_CONFIG_REPO_PATH = Path(APP_USERDATA_DIR, "Config.json")
APP_CONFIG_DAO = TinyConfigDao(path=APP_CONFIG_REPO_PATH)
APP_CONFIG_REPO = ConfigRepo(dao=APP_CONFIG_DAO)
# Create repository if not exists.
if not APP_CONFIG_REPO_PATH.is_file():
    APP_CONFIG_REPO_PATH.touch(exist_ok=False)
