# integration.test_network.test_browser.py
from integration.testhelper import NetworkHelper
from network.browser import BrowserFactory, Browser
from fixtures.selenium import BrowserDriverPathFixture
from unit.testhelper import WebtomatorTestCase


class BrowserFactoryTest(WebtomatorTestCase):
    _netHelper: NetworkHelper

    @classmethod
    def setUpClass(cls) -> None:
        cls._netHelper = NetworkHelper()

    @classmethod
    def tearDownClass(cls) -> None:
        del cls._netHelper

    def test_createChromeShouldReturnBrowserObject(self):
        # Given
        sut = BrowserFactory
        sut.setUserAgentRepo(repo=self._netHelper.userAgentRepo)
        validPath = BrowserDriverPathFixture.CHROME()

        # When
        createdBrowser = sut.createChrome(isHeadless=True, pathToBinary=validPath)

        # Then
        self.assertTrue(isinstance(createdBrowser, Browser),
                        "Expected createdBrowser to be an instance of type Browser "
                        f"but got {createdBrowser}")

        self.assertHasAttribute(createdBrowser, "quit")
        createdBrowser.quit()