# unit.test_shop.test_scraperBstn.py
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import debug.logger as clog
from fixtures.scraper import TEST_BSTN_SHOP_HTML_RESPONSE
from fixtures.scraper import TEST_BSTN_PRODUCT_HTML_RESPONSE
from integration.testhelper import NetworkHelper
from shop.product import Product
from shop.scraperBstn import BstnShopScraper
from shop.shop import Shop
from unit.testhelper import LogHelper
from unit.testhelper import WebtomatorTestCase, TempShopRepoHelper, RequestMock, MessengerMock

if TYPE_CHECKING:
    from pathlib import Path


# TODO ongoing tests
class BstnShopScraperTest(WebtomatorTestCase):
    shopHtmlResponsePath: Path
    productHtmlResponsePath: Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Show some logging while testing, esp. with custom time and sourcecode info
        LogHelper.activate(level=clog.DEBUG)
        # Setup
        cls.shopHtmlResponsePath = TEST_BSTN_SHOP_HTML_RESPONSE.resolve()
        cls.productHtmlResponsePath = TEST_BSTN_PRODUCT_HTML_RESPONSE.resolve()
        # Download shop and product response if both not exist. This is a one-time-op.
        # Note that NetworkHelper is imported from integration tests.
        product = Product(url="https://www.bstn.com/en/adidas-zx-8000-ef4364-147994")
        shop = Shop(name="BSTN Shop Download Response", url="https://www.bstn.com", products=[product])
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
        shop = Shop(name="BSTN Shop unit test", url=str(self.shopHtmlResponsePath))
        product = Product(url=str(self.productHtmlResponsePath))
        shop.addProduct(product)

        # Results will be written to a temp DB file which path is defined in TempShopRepoHelper.
        repoHelper = TempShopRepoHelper(shops=[shop])

        async def runner():
            # Given
            requestMock = RequestMock()
            messengerMock = MessengerMock(request=requestMock)

            sut = BstnShopScraper(
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
