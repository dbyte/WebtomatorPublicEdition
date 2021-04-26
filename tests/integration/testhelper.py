# integration.testhelper.py
from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

import network.messenger as msn
from fixtures.network import TEST_INTEGRATION_PROXIES_REPO_PATH, \
    TEST_USERAGENTS_INTEGRATION_REPO_PATH, TEST_MESSENGERS_INTEGRATION_REPO_PATH
from fixtures.shop import TEMP_SHOPS_TINYDB_TEST_PATH, PRODUCTS_URLS_INTEGRATION_TEST_PATH
from network.connection import AioHttpSession, AioHttpRequest
from network.proxyDao import FileProxyDao
from network.proxyRepo import ProxyRepo
from network.userAgentDao import FileUserAgentDao
from network.userAgentRepo import UserAgentRepo
from shop.productsUrlsDao import ProductsUrlsDao
from shop.productsUrlsRepo import ProductsUrlsRepo
from shop.shopDao import TinyShopDao
from shop.shopRepo import ShopRepo

if TYPE_CHECKING:
    from typing import List
    from pathlib import Path
    from shop.shop import Shop
    from shop.product import Product
    from network.connection import Request


class NetworkHelper:
    """ A factory producing the following fully configured objects (with integration test repos):
    FileProxyDao, ProxyRepo, FileUserAgentDao, UserAgentRepo.

    All objects point to specialized resources for integration testing. """

    def __init__(self):
        self.proxyDao = FileProxyDao(filepath=TEST_INTEGRATION_PROXIES_REPO_PATH)
        self.proxyRepo = ProxyRepo(dao=self.proxyDao)
        self.userAgentDao = FileUserAgentDao(filepath=TEST_USERAGENTS_INTEGRATION_REPO_PATH)
        self.userAgentRepo = UserAgentRepo(dao=self.userAgentDao)
        self.messengerDao = msn.DiscordTinyDao(path=TEST_MESSENGERS_INTEGRATION_REPO_PATH)
        self.messengerRepo = msn.Repo(dao=self.messengerDao)

    def createDiscordMessenger(self, request: Request) -> msn.Discord:
        return msn.Discord(request=request, repo=self.messengerRepo)

    def downloadShopResponse(self, shop: Shop, shopResponsePath: Path, productResponsePath: Path):
        """ Run this to get an up-to-date version of the shop's and products HTML responses
        and let it write into appropriate HTML response fixture files. """

        # Preconditions
        if shopResponsePath.is_file() or productResponsePath.is_file():
            print("Unit test: Skipping download of shop response file fixtures because "
                  "at least one of them they already exists. Paths are:\n"
                  f"{shopResponsePath}\n{productResponsePath}")
            return

        assert isinstance(shop.products, list)
        assert len(shop.products) > 0
        product = shop.products[0]
        assert product.url.startswith("http")

        # Request site and write results to given file paths
        async def runner():
            session = AioHttpSession(proxyRepo=self.proxyRepo,
                                     userAgentRepo=self.userAgentRepo)
            request = AioHttpRequest(session)

            try:
                # 1. Get shop response
                fetchParams = request.Params(url=shop.url)
                response = await request.fetch(params=fetchParams)

                if response.text:
                    soup = BeautifulSoup(response.text, "html.parser")
                    with open(str(shopResponsePath), "w+", encoding="utf-8") as file:
                        file.write(soup.prettify())

                # 2. Get product response
                fetchParams.url = product.url
                response = await request.fetch(params=fetchParams)
                if response.text:
                    soup = BeautifulSoup(response.text, "html.parser")
                    with open(str(productResponsePath), "w+", encoding="utf-8") as file:
                        file.write(soup.prettify())

            finally:
                await session.close()

        if sys.platform == 'win32' and sys.version_info >= (3, 8, 0):
            # Use this workaround on Win for Python >= 3.8, else
            # web proxies won't work with aiohttp.
            # source: https://github.com/aio-libs/aiohttp/issues/2245#issuecomment-545586306
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(runner())


class ConcreteShopHelper:
    """ Helper for shop scraping tests. Is able to create a fully scrapable
    concrete shop. Able to create this shop as a record within a temporary shop repository. """
    shop: Shop

    shopDaoPath = TEMP_SHOPS_TINYDB_TEST_PATH
    shopDao = TinyShopDao(path=shopDaoPath)
    shopRepo = ShopRepo(dao=shopDao)
    productsUrlsRepo: ProductsUrlsRepo

    def __init__(self, shop: Shop, productsUrlsRepoPath: Path):
        self.shop = shop
        self.productsUrlsRepoPath = productsUrlsRepoPath
        assert productsUrlsRepoPath.is_file()
        productsUrlsDao = ProductsUrlsDao(productsUrlsRepoPath)
        self.productsUrlsRepo = ProductsUrlsRepo(dao=productsUrlsDao)

    def assignProductsFromProductsUrlsRepo(self):
        # Generate shop products from products URLs (which are fixtures).
        products = self.productsUrlsRepo.getAll()
        assert len(products) > 0
        if products:
            self.shop.assignProducts(products)
            assert len(self.shop.products) > 0

    def overwriteRepoTableWithScrapableShop(self):
        # Create fresh 'Shops' table with this shop as its data.
        self.assignProductsFromProductsUrlsRepo()
        self.shopRepo.setAll(shops=[self.shop])


class ProductsUrlsRepoMock(ProductsUrlsRepo):
    """ Mocks class ProductsUrlsRepo for integration tests. We are using an integration
    tests URL repository which is allowed to be changed when certain URLs ae not reachable
    anymore or got updated to a different endpoint.
    """

    def __init__(self):
        self.productsUrlsRepoPath = PRODUCTS_URLS_INTEGRATION_TEST_PATH
        assert self.productsUrlsRepoPath.is_file()

        productsUrlsDao = ProductsUrlsDao(filepath=self.productsUrlsRepoPath)
        self.productsUrlsRepo = ProductsUrlsRepo(dao=productsUrlsDao)

        super().__init__(dao=productsUrlsDao)

    def getAllUrls(self) -> List[str]:
        products: List[Product] = self.getAll()
        assert isinstance(products, list)
        assert len(products) > 0
        allProductUrls = [p.url for p in products]
        return allProductUrls
