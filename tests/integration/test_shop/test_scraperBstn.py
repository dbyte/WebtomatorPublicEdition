# unit.test_shop.test_scraperBstn.py
import asyncio

from fixtures.shop import PRODUCTS_URLS_INTEGRATION_TEST_PATH
from integration.testhelper import NetworkHelper, ConcreteShopHelper
from network.connection import AioHttpSession, AioHttpRequest
from shop.scraperBstn import BstnShopScraper
from shop.shop import Shop
from unit.testhelper import WebtomatorTestCase


# TODO ongoing tests
class BstnShopScraperTest(WebtomatorTestCase):
    shopHelper: ConcreteShopHelper
    netHelper: NetworkHelper

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        shop = Shop(name="BSTN", url="https://www.bstn.com")
        cls.shopHelper = ConcreteShopHelper(shop, PRODUCTS_URLS_INTEGRATION_TEST_PATH)
        cls.shopHelper.overwriteRepoTableWithScrapableShop()
        cls.netHelper = NetworkHelper()

    @classmethod
    def tearDownClass(cls):
        del cls.shopHelper, cls.netHelper
        super().tearDownClass()

    def test_run_WithProductionRequest(self):
        """ Does a real network request and sends a webhook message to a real Discord channel.
        Uses integration test fixtures for repository paths. """

        async def runner():
            # Given
            session = AioHttpSession(proxyRepo=self.netHelper.proxyRepo,
                                     userAgentRepo=self.netHelper.userAgentRepo)
            request = AioHttpRequest(session)
            messenger = self.netHelper.createDiscordMessenger(request=request)

            # When
            try:
                sut = BstnShopScraper(
                    scrapee=self.shopHelper.shop,
                    scrapeeRepo=self.shopHelper.shopRepo,
                    request=request,
                    messenger=messenger)

                await sut.run()

            # Then
            except Exception as e:
                self.fail(f"Expected test to run without exception, but got {e}")

            finally:
                await session.close()

        asyncio.run(runner())
