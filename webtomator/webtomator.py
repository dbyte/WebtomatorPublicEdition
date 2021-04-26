#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

import debug.logger as clog
import network.messenger as msn
from network.connection import AioHttpRequest, AioHttpSession
from network.proxyDao import FileProxyDao
from network.proxyRepo import ProxyRepo
from network.userAgentDao import FileUserAgentDao
from network.userAgentRepo import UserAgentRepo
from scraper.base import ScraperFactory
from shop.productsUrlsDao import ProductsUrlsDao
from shop.productsUrlsRepo import ProductsUrlsRepo
from shop.shopDao import TinyShopDao
from shop.shopRepo import ShopRepo
from config.base import APP_CONFIG_REPO, APP_USERDATA_DIR

if TYPE_CHECKING:
    from typing import List, TYPE_CHECKING
    from network.connection import Request, Session
    from scraper.base import Scraper
    from shop.shop import Shop

logger = clog.getLogger(__name__)


class Main:

    def __init__(self):
        self.logfilePath = APP_USERDATA_DIR / "Logs/log_current.txt"
        self.shopsRepoPath = APP_USERDATA_DIR / "Shops.json"
        shopDao = TinyShopDao(path=self.shopsRepoPath)
        self.productsUrlsRepoPath = APP_USERDATA_DIR / "ProductsURLs.txt"
        productsUrlsDao = ProductsUrlsDao(filepath=self.productsUrlsRepoPath)
        self.messengersRepoPath = APP_USERDATA_DIR / "Messengers.json"
        discordMessengerDao = msn.DiscordTinyDao(path=self.messengersRepoPath)
        self.proxiesRepoPath = APP_USERDATA_DIR / "Proxies.txt"
        proxyDao = FileProxyDao(filepath=self.proxiesRepoPath)
        self.userAgentsRepoPath = APP_USERDATA_DIR / "UserAgents.txt"
        userAgentDao = FileUserAgentDao(filepath=self.userAgentsRepoPath)

        self.shopRepo = ShopRepo(dao=shopDao)
        self.productsUrlsRepo = ProductsUrlsRepo(dao=productsUrlsDao)
        self.discordMessengerRepo = msn.Repo(dao=discordMessengerDao)
        self.proxyRepo = ProxyRepo(dao=proxyDao)
        self.userAgentRepo = UserAgentRepo(dao=userAgentDao)

        self.session = None
        self.scrapers: List[Scraper] = list()
        self.shops: List[Shop] = list()

        self._configureLogger()
        self._createRepoFilesIfNotExist()

    async def run(self):
        self._setShops()

        try:
            await self._startHttpSession()
            await self._setScrapers()

            # Create runners, start scraping
            loopRunners = [s.loopRun() for s in self.scrapers]
            await asyncio.gather(*loopRunners)

        finally:
            await self.session.close()

    def _configureLogger(self):
        loggerConfig = APP_CONFIG_REPO.findLoggerConfig()
        clog.configureLogger(logger=clog.getRootLogger(),
                             config=loggerConfig,
                             logfilePath=self.logfilePath)

    def _createRepoFilesIfNotExist(self):
        if not self.shopsRepoPath.is_file():
            self.shopsRepoPath.touch(exist_ok=False)
        if not self.productsUrlsRepoPath.is_file():
            self.productsUrlsRepoPath.touch(exist_ok=False)
        if not self.messengersRepoPath.is_file():
            self.messengersRepoPath.touch(exist_ok=False)
        if not self.proxiesRepoPath.is_file():
            self.proxiesRepoPath.touch(exist_ok=False)
        if not self.userAgentsRepoPath.is_file():
            self.userAgentsRepoPath.touch(exist_ok=False)

    def _setShops(self):
        # Update shop repo by looking through the ProductsUrls repository.
        # This adds and/or deletes repo-shops and/or repo-products which do not correspond to
        # the detected ProductsUrls.
        self.shopRepo.updateFromProductsUrls(productsUrlsRepo=self.productsUrlsRepo)

        try:
            self.shops = self.shopRepo.getAll()

        except Exception as e:
            logger.warning("%s", e, exc_info=True)
            raise

    async def _startHttpSession(self):
        self.session: Session = AioHttpSession(proxyRepo=self.proxyRepo,
                                               userAgentRepo=self.userAgentRepo)

    async def _setScrapers(self):
        if not self.shops:
            raise AttributeError("Unable to create scrapers: Shops are not set.")
        if not self.session:
            raise AttributeError("Unable to create scrapers: Session not set.")

        messengerRequest: Request = AioHttpRequest(session=self.session)
        discordMessenger = msn.Discord(request=messengerRequest, repo=self.discordMessengerRepo)

        scraperFactory = ScraperFactory()
        self.scrapers = scraperFactory.makeFromScrapees(
            scrapees=self.shops,
            scrapeeRepo=self.shopRepo,
            session=self.session,
            requestClass=AioHttpRequest,
            messenger=discordMessenger)

        if not self.scrapers:
            raise LookupError("No scrapers were generated.")


if __name__ == "__main__":
    # Logger not configured at this time, so we print
    print("Webtomator started. Initializing...")

    main = Main()
    logger.info("Webtomator initialized. Your user data directory is %s", APP_USERDATA_DIR)

    try:
        if sys.platform == 'win32' and sys.version_info >= (3, 8, 0):
            # Use this workaround on Win for Python >= 3.8, else
            # web proxies won't work with aiohttp.
            # source: https://github.com/aio-libs/aiohttp/issues/2245#issuecomment-545586306
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main.run())

    except KeyboardInterrupt:
        logger.info("Webtomator ended by KeyboardInterrupt.")

    except Exception as globExc:
        logger.error("Webtomator ended: %s", globExc, exc_info=True)
