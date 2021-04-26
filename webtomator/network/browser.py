# network.browser.py
import platform
from pathlib import Path
from typing import Optional

import debug.logger as clog

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver as SlnWebDriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from config.base import APP_USERDATA_DIR
from network.searchconditions import SearchConditions, Strategy, StrategyAdapter
from network.userAgentRepo import UserAgentRepo

logger = clog.getLogger(__name__)


class Browser:

    def __init__(self, driver: SlnWebDriver):

        logger.info("Initializing webdriver...")
        try:
            self.__driver = driver

        except WebDriverException as e:
            raise BrowserException(f"Webdriver could not be initialized. {e}")

        logger.info("Webdriver initialized")

    # Public methods

    def getPageHTML(self):
        return self.__driver.page_source

    def loadInitialPage(self, url: str):
        self.__driver.get(url)

    def waitForElement(self, searchConditions: SearchConditions, maxSecondsWait: float):
        # Pre check incoming values
        allowedStrategies = [Strategy.BY_ID, Strategy.BY_TEXT]
        if searchConditions.searchStrategy in allowedStrategies:
            strategy = StrategyAdapter(searchConditions.searchStrategy).toSelenium()
        else:
            raise BrowserException(
                f"Search strategy {searchConditions.searchStrategy} not implemented.")

        # Convert identifier corresponding to search strategy
        identifier = ""
        if searchConditions.searchStrategy == Strategy.BY_ID:
            identifier = searchConditions.identifier
        elif searchConditions.searchStrategy == Strategy.BY_TEXT:
            identifier = '//*[contains(text(), "{0}")]'.format(searchConditions.identifier)

        # Tell framework to wait until the asked element appears
        wait = WebDriverWait(self.__driver, maxSecondsWait)
        wait.until(
            ec.visibility_of_element_located(
                (strategy, identifier)
            )
        )

    def sendKeys(self, searchConditions: SearchConditions, text: str):
        element: WebElement = self.getElement(searchConditions)
        if element is None:
            return
        element.send_keys(text)

    def select(self, searchConditions: SearchConditions, text: str):
        element: WebElement = self.getElement(searchConditions)
        if element is None:
            return
        select = Select(element)
        select.select_by_visible_text(text)

    def click(self, searchConditions: SearchConditions):
        element: WebElement = self.getElement(searchConditions)
        if element is None:
            return
        element.click()

    def submit(self, searchConditions: SearchConditions):
        element: WebElement = self.getElement(searchConditions)
        if element is None:
            return
        element.submit()

    def quit(self):
        self.__driver.quit()

    def getElement(self, searchConditions: SearchConditions):
        # Search
        strategy = searchConditions.searchStrategy
        if strategy == Strategy.BY_ID:
            return self.__findFirstElementByID(searchConditions.identifier)

        elif strategy == Strategy.BY_XPATH:
            return self.__findFirstElementByXPath(searchConditions.identifier)

        elif strategy == Strategy.BY_CLASSNAME:
            return self.__findElementByClassname(searchConditions.identifier)

        elif strategy == Strategy.BY_TEXT:
            # ToDo Test
            return self.__findByTextFragment(searchConditions.identifier)

    # Private methods

    def __findFirstElementByXPath(self, xpath: str):
        elements = self.__driver.find_elements_by_xpath(xpath)
        if len(elements) > 0:
            return elements[0]
        return None

    def __findElementByClassname(self, name: str):
        element = self.__driver.find_element_by_class_name(name)
        if element:
            return element
        return None

    def __findFirstElementByID(self, id: str):
        elements = self.__driver.find_elements_by_id(id)
        if len(elements) > 0:
            return elements[0]
        return None

    def __findByTextFragment(self, text: str):
        # ToDo Test
        elements = self.__driver.find_element_by_name(text)
        if len(elements) > 0:
            return elements[0]
        return None

    def __convertStrategyToSelenium(self, strategy: Strategy):
        adapter = StrategyAdapter(strategy=strategy)
        return adapter.toSelenium()


class BrowserFactory:
    __driver = None
    __options = None

    __userAgentRepo = UserAgentRepo()
    """ Default user-agent, may be overridden with setUserAgentRepo(...) """

    @classmethod
    def createDefaultBrowser(cls, isHeadless=True):
        """
        Defines & returns the app's default browser-driver.

        :param isHeadless: True = Browser without visible GUI.
        :return: A Browser object if initialization was successful, else None
        """
        # Change here to switch the default driver.
        return cls.createChrome(isHeadless)

    # Configure Chrome webdriver
    @classmethod
    def createChrome(cls, isHeadless: bool, pathToBinary: Optional[Path] = None):
        """ Configure Chrome webdriver

        :param isHeadless: True = Browser without visible GUI.
        :param pathToBinary: Absolute path to the browser's driver.
        :return: Chrome Browser object if initialization was successful, else None
        """
        # Set default path to chromedriver binary if not given.
        if not pathToBinary:
            if platform.system() == "Windows":
                pathToBinary = Path(
                    APP_USERDATA_DIR, "webdrivers-windows/chromedriver.exe").resolve()

                assert pathToBinary.is_file()

            elif platform.system() == "Darwin":
                pathToBinary = Path("/usr/local/bin/chromedriver").resolve()
                assert pathToBinary.is_file()

            else:
                raise NotImplementedError(f"Webdriver not yet implemented for system {platform.system()}.")

        cls.__options = webdriver.ChromeOptions()
        cls.__addDefaultOptions()
        if isHeadless:
            cls.__addHeadlessOption()

        try:
            cls.__driver = webdriver.Chrome(str(pathToBinary), options=cls.__options)
            cls.__driver.delete_all_cookies()

        except WebDriverException as e:
            print(f"Webdriver could not be initialized. {e}")
            return None

        agent = cls.__driver.execute_script("return navigator.userAgent")
        logger.debug("Random User-Agent: %s", agent)

        return Browser(cls.__driver)

    @classmethod
    def setUserAgentRepo(cls, repo: UserAgentRepo):
        cls.__userAgentRepo = repo

    @classmethod
    def __addHeadlessOption(cls):
        cls.__options.add_argument('--headless')

    @classmethod
    def __addDefaultOptions(cls):
        cls.__options.add_argument('--ignore-certificate-errors')
        cls.__options.add_argument('--incognito')

        randomAgent = cls.__userAgentRepo.getRandomUserAgent()  # raises
        cls.__options.add_argument(f"user-agent={randomAgent}")

        # "--proxy-server=http://user:password@yourProxyServer.com:8080"
        # proxy = "http://rf8u8eozon:Ng8GNCqUFw2YcJNT_country-Germany_session-g4i64cy671@resi" \
        #        ".hawkproxy.com:8080"
        # cls.__options.add_argument(f"--proxy-server={proxy}")


class BrowserException(Exception):
    """ A custom Exception class for our Browser facades """
    pass
