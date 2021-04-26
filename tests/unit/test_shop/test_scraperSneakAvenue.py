# unit.test_shop.test_scraperSneakAvenue.py
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import debug.logger as clog
from fixtures.scraper import TEST_SNEAKAVENUE_PRODUCT_HTML_RESPONSE
from fixtures.scraper import TEST_SNEAKAVENUE_SHOP_HTML_RESPONSE
from integration.testhelper import NetworkHelper
from shop.product import Product
from shop.scraperSneakAvenue import SneakAvenueShopScraper
from shop.shop import Shop
from unit.testhelper import LogHelper
from unit.testhelper import WebtomatorTestCase, TempShopRepoHelper, RequestMock, MessengerMock

if TYPE_CHECKING:
    from pathlib import Path


class SneakAvenueShopScraperTest(WebtomatorTestCase):
    shopHtmlResponsePath: Path
    productHtmlResponsePath: Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Show some logging while testing, esp. with custom time and sourcecode info
        LogHelper.activate(level=clog.DEBUG)
        # Setup
        cls.shopHtmlResponsePath = TEST_SNEAKAVENUE_SHOP_HTML_RESPONSE.resolve()
        cls.productHtmlResponsePath = TEST_SNEAKAVENUE_PRODUCT_HTML_RESPONSE.resolve()
        # Download shop and product response if both not exist. This is a one-time-op.
        # Note that NetworkHelper is imported from integration tests.
        product = Product(url="https://www.sneak-a-venue.de/nike-air-max-95-se-white-229724")
        shop = Shop(name="Sneak-a-venue Shop Unit Test", url="https://www.sneak-a-venue.de/", products=[product])
        netHelper = NetworkHelper()
        netHelper.downloadShopResponse(
            shop=shop,
            shopResponsePath=cls.shopHtmlResponsePath,
            productResponsePath=cls.productHtmlResponsePath)

    @classmethod
    def tearDownClass(cls):
        LogHelper.reset()
        del cls.shopHtmlResponsePath, cls.productHtmlResponsePath
        super().tearDownClass()

    def test_run(self):
        # Given
        shop = Shop(name="Sneak-a-venue Shop unit test", url=str(self.shopHtmlResponsePath))
        product = Product(url=str(self.productHtmlResponsePath))
        shop.addProduct(product)

        # Results will be written to a temp DB file which path is defined in TempShopRepoHelper.
        repoHelper = TempShopRepoHelper(shops=[shop])

        async def runner():
            # Given
            requestMock = RequestMock()
            messengerMock = MessengerMock(request=requestMock)

            sut = SneakAvenueShopScraper(
                scrapee=shop,
                scrapeeRepo=repoHelper.shopRepo,
                request=requestMock,
                messenger=messengerMock
            )

            # When / Then
            try:
                await sut.run()

            except Exception as e:
                self.fail(f"Expected test to run without Exception, but raised: {e}")

            else:
                self.assertEqual(0, sut._failCount,
                                 f"Expected fail count to be 0, but is {sut._failCount}")

        asyncio.run(runner())
