# scraper.base.py
import asyncio
import datetime as dtt
import time
from abc import ABC, abstractmethod
from typing import List, Type

import debug.logger as clog
from config.base import APP_CONFIG_REPO
from network import messenger as msn
from network.connection import Request, Tools, Session

logger = clog.getLogger(__name__)


class Scrapable(ABC):
    """ Interface for classes with the ability to scrape its URL target.
    """

    @property
    @abstractmethod
    def url(self) -> str: ...

    @url.setter
    @abstractmethod
    def url(self, val: str) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @name.setter
    @abstractmethod
    def name(self, val: str) -> None: ...

    @property
    @abstractmethod
    def lastScanStamp(self) -> float: ...

    @lastScanStamp.setter
    @abstractmethod
    def lastScanStamp(self, val: float) -> None: ...

    def setLastScanNow(self) -> None:
        """ Set scan time from current time as float.

        :return: None
        """
        self.lastScanStamp = dtt.datetime.utcnow().timestamp()


class Scraper(ABC):
    """ Scraper base class """

    def __init__(self,
                 scrapee: Scrapable,
                 scrapeeRepo,
                 request: Request,
                 messenger: msn.Discord):

        # Init by params
        self._scrapee = scrapee
        self._scrapeeRepo = scrapeeRepo
        self._request = request  # final configuration by __configureAfterInit
        self._messenger: msn.Discord = messenger

        # Init other instance attributes
        self._isCancelLoop = False
        self._failCount = 0
        self._iterSleep = (30, 40, 0.5)  # finally overridden by __configureAfterInit
        """ Variable sleep time between iterations.
        1st number is minimum seconds, 2nd number is maximum seconds, 3rd number is decimal
        steps between each second.
            |  Example: (20, 30, 0.5)
        This is used to generate a random sleep time, constrained by the 1st and the 2nd number.
        """

        # Do final setup after initialization is done
        self.__configureAfterInit()

    @property
    @abstractmethod
    def URL(self) -> str:
        ...

    """ URL for the remote request. This is meant to be a static constant, hence uppercase! """

    @abstractmethod
    async def run(self) -> None:
        ...

    """ Scrapes the scrapee one single time. Called by `loopRun`. """

    async def loopRun(self) -> None:
        """ Loops over method `run()` and does some work before and after.
        Cancel loop by setting `_isCancelLoop` to True.

        :return: None
        """
        logger.debug("Looper for %s called, will enter loop.", self._scrapee.url)

        i = 0
        while True:
            i += 1
            startTime = time.time()  # Start performance measuring for iteration
            logger.info("Scraper %s: Starting iteration.", self._scrapee.name)

            # Wait until whole worker has completed. Rules for completion are defined
            # within the worker itself. Meanwhile, suspend me for other tasks.
            result = await self.run()

            # Stop performance measuring for iteration
            duration = time.time() - startTime
            logger.info("🔹%s: Iteration %d done.",
                        self._scrapee.name, i)
            logger.debug("Scraper %s iteration took %.2f seconds.", self._scrapee.name, duration)

            if self._isCancelLoop:
                logger.info("🚫 Scraper %s: Cancelled. Exiting loop.", self._scrapee.name)
                break

            randSleep = Tools.getRandomBetween(start=self._iterSleep[0],
                                               stop=self._iterSleep[1],
                                               step=self._iterSleep[2])
            logger.info("Waiting %.2f seconds before running scraper again.", randSleep)
            await asyncio.sleep(randSleep)

    async def sendMessage(self, **kwargs) -> None:
        # Does only send if a messenger object exists
        if self._messenger:
            await self._messenger.send(**kwargs)

        else:
            logger.debug("Won't send message, no messenger configured for this scraper. %s",
                         self._scrapee.url)

    def __configureAfterInit(self) -> None:
        """ Does final configuration for the scraper. This must be AFTER all initialization
        of the instance is done. """
        cfg = APP_CONFIG_REPO.findScraperConfigByUrl(url=self.URL)
        self._iterSleep = (cfg.iterSleepFromScnds, cfg.iterSleepToScnds, cfg.iterSleepSteps)
        self._request.configure(
            timeout=cfg.fetchTimeoutScnds,
            maxRetries=cfg.fetchMaxRetries,
            useRandomProxy=cfg.fetchUseRandomProxy)


class ScraperFactory:

    def __init__(self):
        self._scraperClasses: List[Type[Scraper]] = list()

        # Register all scrapees here
        from shop.scraperFootdistrict import FootdistrictShopScraper
        self.register(FootdistrictShopScraper)
        from shop.scraperSolebox import SoleboxShopScraper
        self.register(SoleboxShopScraper)
        from shop.scraperBstn import BstnShopScraper
        self.register(BstnShopScraper)
        from shop.scraperSneakAvenue import SneakAvenueShopScraper
        self.register(SneakAvenueShopScraper)

    def register(self, class_: Type[Scraper]) -> None:
        """ Appends the given class to an internal list
        of classes which are able to be instantiated by this factory.

        :param class_: The class to register as type (not an instance!)
        :return: None
        """
        if class_ not in self._scraperClasses:
            self._scraperClasses.append(class_)

    def makeFromScrapees(self,
                         scrapees: List[Scrapable],
                         scrapeeRepo,
                         requestClass: Type[Request],
                         session: Session,
                         messenger: msn.Discord) -> List[Scraper]:
        """ Creates a list of ready-to-use scraper objects.
        Return an empty list if no scrapers were created. Returns gracefully. """

        scrapers: List[Scraper] = list()

        if not scrapees:
            logger.warning("Scraper factory: No scrapees were passed in.")
            return scrapers

        for scrapee in scrapees:
            try:
                scraper = self.makeFromScrapee(
                    scrapee=scrapee,
                    scrapeeRepo=scrapeeRepo,
                    requestClass=requestClass,
                    session=session,
                    messenger=messenger)
                scrapers.append(scraper)

            except LookupError as e:
                logger.warning("Scraper factory: %s", e)

        return scrapers

    def makeFromScrapee(self,
                        scrapee: Scrapable,
                        scrapeeRepo,
                        session: Session,
                        requestClass: Type[Request],
                        messenger: msn.Discord) -> Scraper:

        def condition(scraper: Scraper) -> bool:
            return scraper.URL == scrapee.url

        # Search in registered Scrapers. Note that Scraper.url must be a static constant.
        foundScraperClasses = list(filter(condition, self._scraperClasses))

        if not foundScraperClasses:
            raise LookupError(
                f"Expected to find a Scraper but did not find any. "
                f"Scrapee's URL is {scrapee.url}")

        if len(foundScraperClasses) > 1:
            raise LookupError(
                f"Expected one single Scraper but got {len(foundScraperClasses)}. "
                f"Scrapee's URL is {scrapee.url}")

        # Make a Request instance of the given requestClass type.
        # Each scraper needs its own request instance.
        scraperRequest = requestClass(session=session)

        # Initialize Scraper
        instance = foundScraperClasses[0](scrapee=scrapee,
                                          scrapeeRepo=scrapeeRepo,
                                          request=scraperRequest,
                                          messenger=messenger)

        return instance
