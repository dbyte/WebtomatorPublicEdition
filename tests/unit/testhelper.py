# unit.testhelpers.py
import importlib
import unittest
from abc import ABC
from pathlib import Path
from typing import List, ClassVar
from unittest.mock import Mock

import debug.logger as clog
import network.messenger as msn
from config.base import TinyConfigDao, ConfigRepo
from fixtures.scraper import TEST_VALID_CONFIGURATION_PATH
from fixtures.shop import TEMP_SHOPS_TINYDB_TEST_PATH
from network.connection import Request, Session, Response
from shop.productsUrlsDao import ProductsUrlsDao
from shop.productsUrlsRepo import ProductsUrlsRepo
from shop.shop import Shop
from shop.shopDao import TinyShopDao
from shop.shopRepo import ShopRepo


class WebtomatorTestCase(ABC, unittest.TestCase):
    """Base class for all Webtomator tests. """

    @classmethod
    def setUpClass(cls) -> None:
        ScraperConfigRepoMonkeyPatch.start()

    @classmethod
    def tearDownClass(cls) -> None:
        ScraperConfigRepoMonkeyPatch.stop()

    def assertHasAttribute(self, obj, attr_name: str, message=None):
        if not hasattr(obj, attr_name):
            if message is not None:
                self.fail(message)
            else:
                self.fail('{} should have an attribute {}'.format(obj, attr_name))


class LogHelper:
    rootLogger = None

    @classmethod
    def activate(cls, level: int):
        # Show some logging while testing, esp. with custom time and sourcecode info
        cls.rootLogger = clog.getRootLogger()
        cls.rootLogger.setLevel(level)
        cls.rootLogger.addHandler(clog.WarnAndAboveStreamHandler())
        cls.rootLogger.addHandler(clog.DebugAndInfoStreamHandler())

    @classmethod
    def reset(cls):
        cls.rootLogger.setLevel(clog.WARN)
        cls.rootLogger.removeHandler(clog.WarnAndAboveStreamHandler())
        cls.rootLogger.removeHandler(clog.DebugAndInfoStreamHandler())


class TempShopRepoHelper:
    """ Helper for creating a controlling a fully scrapable temporary TinyDB shop repo.
    The repository is created at initialization. It uses a path to a fixture file.
    The shops table is overridden with data passed by the 'shops' argument at initialization. """

    shopDaoPath: ClassVar[Path] = TEMP_SHOPS_TINYDB_TEST_PATH
    shopDao: ClassVar[TinyShopDao] = TinyShopDao(path=shopDaoPath)
    shopRepo: ClassVar[ShopRepo] = ShopRepo(dao=shopDao)

    def __init__(self, shops: List[Shop]):
        self.shops = shops
        self.shopRepo.setAll(shops=self.shops)


class ProductsUrlsRepoMock(ProductsUrlsRepo):

    def __init__(self, productsUrlsRepoPath: Path):
        assert productsUrlsRepoPath.is_file()
        productsUrlsDao = ProductsUrlsDao(filepath=productsUrlsRepoPath)
        super().__init__(dao=productsUrlsDao)


class RequestMock(Request):
    """ Mocks the Request class. Using it instead of the real class enables us to test without
     any network connection, any session handling, nor a specific network library. """

    def __init__(self, session=Mock(spec=Session)):
        super().__init__(session=session)

    async def fetch(self, params: Request.Params, callCount=0) -> Response:
        """
        :param params: See class `Request.Params`
        :param callCount: Counts recursive calls, must be 0 at initial call
        :return: Response object
        """
        if not params.url:
            msg = "RequestMock: Need a file path to the response html file. " \
                  "Pass in the value with param 'url'."
            response = Response(data=None, text=None, error=ValueError(msg))
            return response

        with open(str(Path(params.url)), "r", encoding='utf-8') as htmlFile:
            response = Response(data="No data, response has been created by mock.",
                                text=htmlFile.read(),
                                error=None)
            return response

    async def post(self, params: Request.Params, callCount=0) -> 'Response':
        """ Post a request.

        :param params: See class `Request.Params`
        :param callCount: Counts recursive calls, must be 0 at initial call.
        :return: Response object
        """
        # Not yet implemented. By now, this is just a call to the
        # abstract method, which does nothing.
        await super().post(params=params, callCount=callCount)

        return Response(data="data: unit test mock data",
                        text="text: unit test mock test",
                        error=None)


class MessengerMock(msn.Discord):

    def __init__(self, request: Request):
        super().__init__(request=request, repo=Mock())

    async def send(self, **kwargs):
        pass


class ScraperConfigRepoMonkeyPatch:

    @staticmethod
    def start():
        import scraper.base
        dao = TinyConfigDao(path=TEST_VALID_CONFIGURATION_PATH)
        configRepoFixture = ConfigRepo(dao=dao)
        # Monkey patch
        scraper.base.APP_CONFIG_REPO = configRepoFixture

    @staticmethod
    def stop():
        import scraper.base
        # Reset monkey patch by reloading patched module
        importlib.reload(scraper.base)
