# test_network.test_browser.py

import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import selenium
from selenium.webdriver.remote.webelement import WebElement

import network
from network.browser import BrowserFactory, Browser
from network.searchconditions import SearchConditions, StrategyAdapter, Strategy
from unit.testhelper import WebtomatorTestCase


class BrowserTest(WebtomatorTestCase):
    sut: Browser
    DRIVER_MOCK: Mock

    def setUp(self) -> None:
        self.DRIVER_MOCK = Mock(spec_set=selenium.webdriver.Chrome)
        self.sut: Browser = Browser(driver=self.DRIVER_MOCK)

    def tearDown(self):
        del self.DRIVER_MOCK
        del self.sut

    def test_getPageHTML_shouldReturnPageSource(self):
        # Given
        expectedResult = "<html>Just a test value</html>"
        self.DRIVER_MOCK.page_source.return_value = expectedResult

        # When
        result = self.sut.getPageHTML()

        # Then test if driver method was called and returned the expected return value
        self.assertEqual(expectedResult, result.return_value)

    def test_loadInitialPage_shouldCallGet(self):
        # Given
        expectedURL = "https://some.test.url"
        self.DRIVER_MOCK.get.return_value = expectedURL

        # When
        self.sut.loadInitialPage(expectedURL)

        # Then test if driver method was called and returned the expected return value
        self.DRIVER_MOCK.get.assert_called_once_with(expectedURL)

    def test_waitFor_shouldCallWaitUntil(self):
        # Given
        implementedStrategies = [Strategy.BY_ID, Strategy.BY_TEXT]

        for strategy in implementedStrategies:
            adaptedStrategy = StrategyAdapter(strategy).toSelenium()

            searchConditions = Mock(spec_set=SearchConditions)
            searchConditions.identifier = "//*This is is a test element id"
            searchConditions.searchStrategy = strategy
            maxWait = 0.6  # actually we won't wait here - we just test if value gets passed over

            with mock.patch('network.browser.WebDriverWait', spec=network.browser.WebDriverWait) as waiter:
                with mock.patch('network.browser.ec', spec=network.browser.ec) as ec:
                    # When
                    self.sut.waitForElement(searchConditions=searchConditions,
                                            maxSecondsWait=maxWait)

                    # Then
                    try:
                        generatedIdentifier = ec.method_calls[0][1][0][1]
                    except IndexError:
                        self.fail("Expected call chain was not called. "
                                  "visibility_of_element_located(...) was not called as expected.")

                    self.assertTrue(searchConditions.identifier in generatedIdentifier,
                                    f"Expected identifier '{searchConditions.identifier}' to be part "
                                    f"of argument when initializing "
                                    f"'visibility_of_element_located(...)', but it is not a "
                                    f"substring of {generatedIdentifier}.")

                    ec.visibility_of_element_located.assert_called_with(
                        (adaptedStrategy, generatedIdentifier)
                    )
                    waiter.assert_called_with(self.DRIVER_MOCK, maxWait)
                    waiter().until.assert_called_once_with(ec.visibility_of_element_located())

    def test_waitFor_shouldRaiseTimeout(self):
        # Given
        def raiseError(_, maxWait):
            self.assertEqual(expectedMaxWait, maxWait,
                             "Init of WebDriverWait() should have been "
                             f"initialized with {expectedMaxWait} but was "
                             f"initialized with {maxWait}")
            raise TimeoutError

        expectedMaxWait = 2.3
        searchConditions = Mock(spec_set=SearchConditions)
        searchConditions.searchStrategy = Strategy.BY_ID

        with mock.patch('network.browser.WebDriverWait', spec=network.browser.WebDriverWait) as waiter:
            # When WebDriverWait gets initialized inside the called method, we raise an exception
            waiter.side_effect = raiseError

            # When / Then
            with self.assertRaises(TimeoutError):
                self.sut.waitForElement(searchConditions=searchConditions,
                                        maxSecondsWait=expectedMaxWait)

    def test_sendKeys(self):
        # Given that element was found
        textToSend = "This is a test text to send via sendKeys"
        searchConditions = Mock(spec_set=SearchConditions)
        foundElement = Mock(spec_set=WebElement)
        self.sut.getElement = Mock(return_value=foundElement, autospec=True)

        # When
        self.sut.sendKeys(searchConditions=searchConditions, text=textToSend)

        # Then
        self.sut.getElement.assert_called_once_with(searchConditions)
        foundElement.send_keys.assert_called_once_with(textToSend)

        # Given that element was not found
        foundElement.send_keys.reset_mock()
        self.sut.getElement = Mock(return_value=None, autospec=True)

        # When
        self.sut.sendKeys(searchConditions=searchConditions, text=textToSend)

        # Then
        foundElement.send_keys.assert_not_called()

    def test_click(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        foundElement = Mock(spec_set=WebElement)
        self.sut.getElement = Mock(return_value=foundElement)

        # When
        self.sut.click(searchConditions=searchConditions)

        # Then
        self.sut.getElement.assert_called_once_with(searchConditions)
        foundElement.click.assert_called_once_with()

        # Given that element was not found
        foundElement.click.reset_mock()
        self.sut.getElement = Mock(return_value=None)

        # When
        self.sut.click(searchConditions=searchConditions)

        # Then
        foundElement.click.assert_not_called()

    def test_submit(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        foundElement = Mock(spec_set=WebElement)
        self.sut.getElement = Mock(return_value=foundElement)

        # When
        self.sut.submit(searchConditions=searchConditions)

        # Then
        self.sut.getElement.assert_called_once_with(searchConditions)
        foundElement.submit.assert_called_once_with()

        # Given that element was not found
        foundElement.submit.reset_mock()
        self.sut.getElement = Mock(return_value=None)

        # When
        self.sut.submit(searchConditions=searchConditions)

        # Then
        foundElement.submit.assert_not_called()

    def test_select(self):
        # Given that element was found
        textToSend = "Visible Menu Text"
        searchConditions = Mock(spec_set=SearchConditions)
        foundElement = Mock(spec_set=WebElement)
        foundElement.tag_name = "select"
        self.sut.getElement = Mock(return_value=foundElement)
        seleniumPatchPath = "selenium.webdriver.support.select.Select.select_by_visible_text"

        # When
        with mock.patch(seleniumPatchPath) as select_by_visible_text:
            self.sut.select(searchConditions=searchConditions, text=textToSend)

        # Then
        self.sut.getElement.assert_called_once_with(searchConditions)
        select_by_visible_text.assert_called_once_with(textToSend)

        # Given that element was not found
        foundElement.reset_mock()
        self.sut.getElement = Mock(return_value=None)

        # When
        with mock.patch(seleniumPatchPath) as select_by_visible_text:
            self.sut.select(searchConditions=searchConditions, text=textToSend)

        # Then
        select_by_visible_text.assert_not_called()

    def test_quit(self):
        # Given
        self.DRIVER_MOCK.quit = Mock()

        # When
        self.sut.quit()

        # Then
        self.DRIVER_MOCK.quit.assert_called_once_with()

    def test_getElement(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)

        # When
        self.sut.getElement(searchConditions=searchConditions)

        # Then


class BrowserFactoryTest(WebtomatorTestCase):

    def test_createDefaultBrowser_shouldCallCreateChrome(self):
        # Given
        sut = BrowserFactory
        isHeadless = False

        # When
        with mock.patch('network.browser.BrowserFactory.createChrome') as createChrome:
            sut.createDefaultBrowser(isHeadless=isHeadless)

        # Then
        createChrome.assert_called_once()
        createChrome.assert_called_with(isHeadless)

    def test_createChrome_should_return_None_if_browserextension_not_found(self):
        # Given
        sut = BrowserFactory
        invalidPath = Path("/usr-xxx/local-xxx/bin-xxx/chromedriver-xxx")

        # When
        deliveredObject = sut.createChrome(isHeadless=True, pathToBinary=invalidPath)

        # Then
        self.assertEqual(type(None), type(deliveredObject),
                         f"Expected NoneType but got {deliveredObject}")


if __name__ == '__main__':
    unittest.main()
