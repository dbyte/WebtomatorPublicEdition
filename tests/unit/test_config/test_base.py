# unit.test_config.test_base.py
from config.base import TinyConfigDao, ScraperConfig, ConfigRepo, LoggerConfig
from fixtures.scraper import TEST_EMPTY_DATABASE_CONFIGURATION_PATH
from fixtures.scraper import TEST_VALID_CONFIGURATION_PATH
from unit.testhelper import WebtomatorTestCase


class LoggerConfigTest(WebtomatorTestCase):

    def test_init(self):
        # When / Then
        try:
            LoggerConfig(
                isConsoleLogging=False,
                isFileLogging=True,
                consoleLogLevel=20,
                fileLogLevel=10)

        except Exception as e:
            self.fail("Expected initialization of LoggerConfig to run without "
                      f"errors, but raised {e}")


class ScraperConfigTest(WebtomatorTestCase):

    def test_init(self):
        # When / Then
        try:
            ScraperConfig(
                iterSleepFromScnds=1,
                iterSleepToScnds=2,
                iterSleepSteps=0.3,
                fetchTimeoutScnds=10,
                fetchMaxRetries=5,
                fetchUseRandomProxy=False,
                postTimeoutScnds=6,
                postMaxRetries=3,
                postUseRandomProxies=True)

        except Exception as e:
            self.fail("Expected initialization of ScraperConfig to run without "
                      f"errors, but raised {e}")


class TinyConfigDaoTest(WebtomatorTestCase):

    def test_find_shouldRaiseOnInvalidArgumentKey(self):
        # Given
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)

        # When / Then
        with self.assertRaises(KeyError):
            with dao as sut:
                sut.find(someInvalidParamKey="")  # noqa

    def test_find_loggerConfig(self):
        # Given
        import debug.logger as clog
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)
        # Expect data of the fixture file
        expectedConfig = LoggerConfig(
            isConsoleLogging=True,
            isFileLogging=False,
            consoleLogLevel=clog.DEBUG,
            fileLogLevel=clog.NOTSET)

        # When
        with dao as sut:
            foundConfig = sut.find(loggerConfig=True)

        # Then
        self.assertEqual(expectedConfig, foundConfig)

    def test_find_loggerConfig_shouldFallbackToRescueDefaultsIfNotFound(self):
        # Given
        import debug.logger as clog
        dao = TinyConfigDao(path=TEST_EMPTY_DATABASE_CONFIGURATION_PATH)
        # Expect hard coded data
        expectedRescueConfig = LoggerConfig(
            isConsoleLogging=True,
            isFileLogging=False,
            consoleLogLevel=clog.INFO,
            fileLogLevel=clog.NOTSET)

        # When
        with dao as sut:
            foundConfig = sut.find(loggerConfig=True)

        # Then
        self.assertEqual(expectedRescueConfig, foundConfig)

    def test_find_scraperConfigByUrl(self):
        # Given
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)

        # ---------- Test 1 ----------

        scraperUrl_01 = "https://www.test_scraper_config_01.com"
        # Expect data of the fixture file
        expectedConfig_01 = ScraperConfig(
            iterSleepFromScnds=8,
            iterSleepToScnds=15,
            iterSleepSteps=0.5,
            fetchTimeoutScnds=8,
            fetchMaxRetries=4,
            fetchUseRandomProxy=True,
            postTimeoutScnds=7,
            postMaxRetries=3,
            postUseRandomProxies=True)

        # When
        with dao as sut:
            foundConfig_01 = sut.find(scraperConfigByUrl=scraperUrl_01)
        # Then
        self.assertEqual(expectedConfig_01, foundConfig_01)

        # ---------- Test 2 ----------

        # Given
        scraperUrl_02 = "https://www.test_scraper_config_02.com"
        # Expect data of the fixture file
        expectedConfig_02 = ScraperConfig(
            iterSleepFromScnds=7,
            iterSleepToScnds=16,
            iterSleepSteps=1.0,
            fetchTimeoutScnds=5,
            fetchMaxRetries=5,
            fetchUseRandomProxy=False,
            postTimeoutScnds=9,
            postMaxRetries=2,
            postUseRandomProxies=False)

        # When
        with dao as sut:
            foundConfig_02 = sut.find(scraperConfigByUrl=scraperUrl_02)
        # Then
        self.assertEqual(expectedConfig_02, foundConfig_02)

    def test_find_scraperConfigByUrl_ShouldFallbackToPersistentDefault(self):
        # Given
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)
        nonExistingScraperConfigUrl = "https://www.this-scraper-default-does-not-exist.org"
        # Expect data of the fixture file
        expectedDefaultConfig = ScraperConfig(
            iterSleepFromScnds=25,
            iterSleepToScnds=35,
            iterSleepSteps=1.0,
            fetchTimeoutScnds=8,
            fetchMaxRetries=5,
            fetchUseRandomProxy=True,
            postTimeoutScnds=7,
            postMaxRetries=4,
            postUseRandomProxies=True)

        # When
        with dao as sut:
            foundDefaultConfig = sut.find(scraperConfigByUrl=nonExistingScraperConfigUrl)
        # Then
        self.assertEqual(expectedDefaultConfig, foundDefaultConfig)

    def test_find_scraperCommonConfig(self):
        # Given
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)
        # Expect data of the fixture file
        expectedDefaultConfig = ScraperConfig(
            iterSleepFromScnds=25,
            iterSleepToScnds=35,
            iterSleepSteps=1.0,
            fetchTimeoutScnds=8,
            fetchMaxRetries=5,
            fetchUseRandomProxy=True,
            postTimeoutScnds=7,
            postMaxRetries=4,
            postUseRandomProxies=True)

        # When
        with dao as sut:
            foundDefaultConfig = sut.find(scraperCommonConfig=True)

        # Then
        self.assertEqual(expectedDefaultConfig, foundDefaultConfig)

    def test_find_scraperCommonConfig_shouldFallbackToRescueDefaultsIfNotFound(self):
        # Given
        dao = TinyConfigDao(path=TEST_EMPTY_DATABASE_CONFIGURATION_PATH)
        # Expect hard coded data
        expectedRescueConfig = ScraperConfig(
            iterSleepFromScnds=20,
            iterSleepToScnds=30,
            iterSleepSteps=0.5,
            fetchTimeoutScnds=8,
            fetchMaxRetries=4,
            fetchUseRandomProxy=True,
            postTimeoutScnds=8,
            postMaxRetries=4,
            postUseRandomProxies=True)

        # When
        with dao as sut:
            foundDefaultConfig = sut.find(scraperCommonConfig=True)

        # Then
        self.assertEqual(expectedRescueConfig, foundDefaultConfig)


class ConfigRepoTest(WebtomatorTestCase):
    testConfigDao: TinyConfigDao

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.testConfigDao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        del cls.testConfigDao
        super().tearDownClass()

    def test_findLoggerConfig(self):
        # Given
        import debug.logger as clog
        sut = ConfigRepo(dao=self.testConfigDao)
        # Expect data of the fixture file
        expectedConfig = LoggerConfig(
            isConsoleLogging=True,
            isFileLogging=False,
            consoleLogLevel=clog.DEBUG,
            fileLogLevel=clog.NOTSET)

        # When
        foundConfig = sut.findLoggerConfig()

        # Then
        self.assertEqual(expectedConfig, foundConfig)

    def test_findScraperConfigByUrl(self):
        # Given
        sut = ConfigRepo(dao=self.testConfigDao)
        scraperUrl = "https://www.test_scraper_config_01.com"
        # Expect data of the fixture file
        expectedConfig = ScraperConfig(
            iterSleepFromScnds=8,
            iterSleepToScnds=15,
            iterSleepSteps=0.5,
            fetchTimeoutScnds=8,
            fetchMaxRetries=4,
            fetchUseRandomProxy=True,
            postTimeoutScnds=7,
            postMaxRetries=3,
            postUseRandomProxies=True)

        # When
        foundConfig = sut.findScraperConfigByUrl(url=scraperUrl)

        # Then
        self.assertEqual(expectedConfig, foundConfig)

    def test_findScraperCommonConfig(self):
        # Given
        sut = ConfigRepo(dao=self.testConfigDao)
        # Expect data of the fixture file
        expectedDefaultConfig = ScraperConfig(
            iterSleepFromScnds=25,
            iterSleepToScnds=35,
            iterSleepSteps=1.0,
            fetchTimeoutScnds=8,
            fetchMaxRetries=5,
            fetchUseRandomProxy=True,
            postTimeoutScnds=7,
            postMaxRetries=4,
            postUseRandomProxies=True)

        # When
        foundDefaultConfig = sut.findScraperCommonConfig()

        # Then
        self.assertEqual(expectedDefaultConfig, foundDefaultConfig)
