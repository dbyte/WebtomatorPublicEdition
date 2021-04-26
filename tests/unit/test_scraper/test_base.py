# unit.test_scraper.test_base.py
from __future__ import annotations

import asyncio
import datetime as dtt
from asyncio import Future
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import Mock

from network.connection import Request, Session
from scraper.base import ScraperFactory, Scrapable, Scraper
from shop.product import Product
from shop.shop import Shop
from shop.shopRepo import ShopRepo
from unit.testhelper import WebtomatorTestCase, MessengerMock, RequestMock

if TYPE_CHECKING:
    from typing import Optional, Type, List


class ScrapableTest(WebtomatorTestCase):
    class ScrapableTestImpl(Scrapable):

        def __init__(self):
            self.__url = "http://something.com"
            self.__name = "My super duper test name"
            self.__lastScanStamp = 1234567.987654321

        @property
        def url(self) -> str:
            return self.__url

        @url.setter
        def url(self, val: str) -> None:
            self.__url = val

        @property
        def name(self) -> str:
            return self.__name

        @name.setter
        def name(self, val: str) -> None:
            self.__name = val

        @property
        def lastScanStamp(self) -> float:
            return self.__lastScanStamp

        @lastScanStamp.setter
        def lastScanStamp(self, val: float) -> None:
            self.__lastScanStamp = val

    def test_derivedShouldBeOfTypeScrapable(self):
        # Given
        sut: Scrapable = self.ScrapableTestImpl()

        # Then
        self.assertIsInstance(sut, Scrapable)

    def test_url_shouldGetAndSet(self):
        # Given
        sut: Scrapable = self.ScrapableTestImpl()

        # When Getter
        self.assertEqual("http://something.com", sut.url)

        # When Setter
        sut.url = "https://new-url.com"
        # Then
        self.assertEqual("https://new-url.com", sut.url)

    def test_name_shouldGetAndSet(self):
        # Given
        sut: Scrapable = self.ScrapableTestImpl()

        # When Getter
        self.assertEqual("My super duper test name", sut.name)

        # When Setter
        sut.name = "A new name for a scrapee"
        # Then
        self.assertEqual("A new name for a scrapee", sut.name)

    def test_lastScanStamp_shouldGetAndSet(self):
        # Given
        sut: Scrapable = self.ScrapableTestImpl()

        # When Getter
        self.assertEqual(1234567.987654321, sut.lastScanStamp)

        # When Setter
        sut.lastScanStamp = 0.123
        # Then
        self.assertEqual(0.123, sut.lastScanStamp)

    def test_setLastScanNow_shouldSetCurrentUTCTimestamp(self):
        # Given
        sut = self.ScrapableTestImpl()
        givenDatetime = dtt.datetime(2029, 1, 30, 15, 00, 00, 00000)
        expectedTimestamp: float = givenDatetime.timestamp()

        with mock.patch("scraper.base.dtt", autospec=True) as mockDatetime:
            mockDatetime.datetime.utcnow.return_value = givenDatetime
            sut.setLastScanNow()

        # Then
        self.assertEqual(expectedTimestamp, sut.lastScanStamp)


class ScraperTest(WebtomatorTestCase):
    class ScraperTestImpl(Scraper):
        URL = "https://www.test_scraper_config_01.com"
        scrapee: Shop

        def __init__(self, scrapee: Shop, scrapeeRepo, request: Request, messenger):

            super().__init__(scrapee=scrapee,
                             scrapeeRepo=scrapeeRepo,
                             request=request,
                             messenger=messenger)

        async def run(self) -> None:
            await super().run()

        @classmethod
        def getInstance(cls) -> Scraper:
            givenScrapee = Mock(spec_set=Shop)
            givenScrapee.url = "https://www.test_scraper_config_01.com"
            givenScrapee.name = "ScraperTestImpl Shop"

            givenScrapeeRepo = Mock(spec_set=ShopRepo)
            givenRequest = RequestMock()
            givenMessenger = MessengerMock(request=givenRequest)

            instance = cls(scrapee=givenScrapee,
                           scrapeeRepo=givenScrapeeRepo,
                           request=givenRequest,
                           messenger=givenMessenger)

            return instance

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Scraper

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'URL')
        self.assertHasAttribute(sut, 'run')
        self.assertHasAttribute(sut, 'loopRun')
        self.assertHasAttribute(sut, 'sendMessage')

    def test_init_shouldSetCorrectValues(self):
        # Given
        givenScrapee = Mock(spec_set=Shop)
        givenScrapeeRepo = Mock(spec_set=ShopRepo)
        givenRequest = RequestMock()
        givenMessenger = MessengerMock(request=givenRequest)

        givenScrapee.url = "https://www.test_scraper_config_01.com"
        givenScrapee.name = "Tremendous shop"

        # Expecting values from ScraperConfigRepoMonkeyPatch repository for
        # scraper URL https://www.test_scraper_config_01.com
        expectedIterSleep = (8, 15, 0.5)
        expectedRequestTimeout = 8
        expectedRequestMaxRetries = 4
        expectedRequestUseRandomProxy = True

        # When
        sut: Scraper = self.ScraperTestImpl(scrapee=givenScrapee,
                                            scrapeeRepo=givenScrapeeRepo,
                                            request=givenRequest,
                                            messenger=givenMessenger)

        # Then
        self.assertIs(sut._scrapee, givenScrapee)
        self.assertEqual(givenScrapee.url, sut._scrapee.url)
        self.assertEqual(givenScrapee.name, sut._scrapee.name)
        self.assertIsInstance(sut._scrapeeRepo, ShopRepo)
        self.assertIsInstance(sut._request, Request)
        self.assertIsInstance(sut._messenger, MessengerMock)
        # Other attributes which are not initializable from outside
        self.assertEqual(False, sut._isCancelLoop)
        self.assertEqual(0, sut._failCount)
        self.assertEqual(expectedIterSleep, sut._iterSleep)
        self.assertEqual(expectedRequestTimeout, sut._request._timeout)
        self.assertEqual(expectedRequestMaxRetries, sut._request._maxRetries)
        self.assertEqual(expectedRequestUseRandomProxy, sut._request._useRandomProxy)

    def test_run_shouldBeCallable(self):
        # Given
        sut: Scraper = self.ScraperTestImpl.getInstance()

        # When
        try:
            asyncio.run(sut.run())

        except Exception as e:
            self.fail(f"Expected 'Scraper().run()' to be callable. {e}")

    def test_loopRun(self):
        # Given
        sut: Scraper = self.ScraperTestImpl.getInstance()
        sut._iterSleep = (0, 1, 0.5)

        async def cancelLoopAfterOneSecond():
            await asyncio.sleep(1)
            sut._isCancelLoop = True

        async def test():
            concurrentCoros = (sut.loopRun(), cancelLoopAfterOneSecond())
            for f in asyncio.as_completed(concurrentCoros, timeout=2):
                await f  # The 'await' may raise

        # When
        try:
            asyncio.run(test())

        except Exception as e:
            self.fail(f"Expected 'Scraper().loopRun()' to be callable and being able to be  "
                      f"cancelled. Did NOT cancel after 2 seconds. {e}")

    def test_sendMessage_shouldCallMessengerSend(self):
        # Given
        sut: Scraper = self.ScraperTestImpl.getInstance()
        productMock = Mock(spec_set=Product)
        shopMock = Mock(spec_set=Shop)

        async def test():
            # When
            with mock.patch("unit.testhelper.MessengerMock.send") as send:
                fut = Future()
                fut.set_result(True)
                send.return_value = fut
                await sut.sendMessage(productMsg=productMock, shop=shopMock)

                # Then
                send.assert_called_once_with(productMsg=productMock, shop=shopMock)

        asyncio.run(test())

    def test_sendMessage_shouldSkipWhenNoMessengerSet(self):
        # Given
        sut: Scraper = self.ScraperTestImpl.getInstance()
        sut._messenger = None

        async def test():
            # When
            with mock.patch("unit.testhelper.MessengerMock.send") as messengerSend:
                await sut.sendMessage(logMsg="Some log text")

                # Then
                messengerSend.assert_not_called()

        asyncio.run(test())


class ScraperFactoryTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.scraperStubClass: Optional[Type[Scraper]] = None

    def tearDown(self) -> None:
        del self.scraperStubClass

    def test_init_shouldSetExpectedValues(self):
        # When
        sut = ScraperFactory()

        # Then
        self.assertIsInstance(sut._scraperClasses, list)
        self.assertLessEqual(1, len(sut._scraperClasses))
        for class_ in sut._scraperClasses:
            self.assertIsInstance(class_, type)
            self.assertTrue(issubclass(class_, Scraper),
                            f"{class_} must be a subclass of Scraper but is not.")

    def test_register(self):
        # Given
        sut = ScraperFactory()
        shopScrapee = Mock(spec_set=Shop)
        shopRepo = Mock(spec_set=ShopRepo)
        request = Mock(spec_set=Request)
        shopScrapee.url = "https://my-supershop.url.com/"
        shopScrapee.name = "The Test Shop"

        # Then
        # Expect that there are one or more scraperClasses
        self.assertGreaterEqual(len(sut._scraperClasses), 1, "Expected at least 1 Scraper class.")

        # Expect that all registered scrapers are constrained to Interface 'Scrapable'.
        for scraperClass in sut._scraperClasses:
            self.assertTrue(issubclass(scraperClass, Scraper))

        for scraperClass in sut._scraperClasses:
            try:
                # Expect that scraperClass is initializable
                # Initialize class:
                scraper = scraperClass(scrapee=shopScrapee,
                                       scrapeeRepo=shopRepo,
                                       request=request,
                                       messenger=Mock())
            except Exception as e:
                self.fail(f"'scraper' object expected to be initializable, but raised: {e}")

            # Expect that scrapee and its URL were correctly passed to scraper
            self.assertIs(scraper._scrapee, shopScrapee)
            self.assertIs(scraper._scrapeeRepo, shopRepo)
            self.assertIs(scraper._request, request)
            self.assertEqual(shopScrapee.url, scraper._scrapee.url)
            self.assertEqual(shopScrapee.name, scraper._scrapee.name)

    def test_register_shouldNotRegisterClassesTwice(self):
        # Given
        sut = ScraperFactory()
        self.scraperStubClass = Mock(spec_set=Scraper)

        # When
        # Multiple registering expected to be ignored by register()
        sut.register(self.scraperStubClass)
        sut.register(self.scraperStubClass)

        # Then
        foundScraperMocks = list(
            filter(lambda typ: typ is self.scraperStubClass, sut._scraperClasses))

        self.assertEqual(1, len(foundScraperMocks))

    def test_makeFromScrapee(self):
        # Given
        sut = ScraperFactory()

        class ScraperStub(Scraper):
            URL = "https://www.test_scraper_config_02.com"

            def __init__(self, scrapee, scrapeeRepo, request: Request, messenger):

                super().__init__(scrapee=scrapee,
                                 scrapeeRepo=scrapeeRepo,
                                 request=request,
                                 messenger=messenger)

            def run(self) -> None:
                raise NotImplementedError

        self.scraperStubClass = ScraperStub
        scrapee = Mock(spec_set=Scrapable)
        scrapeeRepo = Mock(spec_set=ShopRepo)
        session = Mock(spec=Session)
        messengerRequest = RequestMock()
        messenger = MessengerMock(request=messengerRequest)

        # Expecting values from ScraperConfigRepoMonkeyPatch repository for
        # scraper URL https://www.test_scraper_config_02.com
        expectedIterSleep = (7, 16, 1.0)
        expectedRequestTimeout = 5
        expectedRequestMaxRetries = 5
        expectedRequestUseRandomProxy = False

        scrapee.url = "https://www.test_scraper_config_02.com"
        scrapee.name = "The huge factory shop"
        sut.register(class_=self.scraperStubClass)

        # When
        createdScraper = sut.makeFromScrapee(
            scrapee=scrapee,
            scrapeeRepo=scrapeeRepo,
            requestClass=RequestMock,
            session=session,
            messenger=messenger)

        # Then
        self.assertIsInstance(createdScraper, self.scraperStubClass)
        self.assertIsInstance(createdScraper._scrapeeRepo, ShopRepo)
        self.assertIsInstance(createdScraper._request, Request)
        self.assertEqual(self.scraperStubClass.URL, createdScraper.URL)
        self.assertEqual(scrapee.name, createdScraper._scrapee.name)
        # Other attributes which are not initializable from outside
        self.assertEqual(False, createdScraper._isCancelLoop)
        self.assertEqual(0, createdScraper._failCount)
        self.assertEqual(expectedIterSleep, createdScraper._iterSleep)
        self.assertEqual(expectedRequestTimeout, createdScraper._request._timeout)
        self.assertEqual(expectedRequestMaxRetries, createdScraper._request._maxRetries)
        self.assertEqual(expectedRequestUseRandomProxy, createdScraper._request._useRandomProxy)

    def test_makeFromScrapee_shouldRaiseOnScraperNotFound(self):
        # Given
        sut = ScraperFactory()
        nonFindableScrapee = Mock(spec_set=Scrapable)
        nonFindableScrapee.url = "https://non-findable-url.com"

        # When / Then
        with self.assertRaises(LookupError):
            sut.makeFromScrapee(
                scrapee=nonFindableScrapee,
                scrapeeRepo=Mock(),
                requestClass=Mock,
                session=Mock(),
                messenger=Mock())

    def test_makeFromScrapee_shouldRaiseOnMultipleScrapersFound(self):
        # Given
        sut = ScraperFactory()
        scrapee = Mock(spec_set=Scrapable)
        scrapee.url.return_value = "does not matter here"

        class ScraperStub(Scraper):
            URL: str = "does not matter here"

            def run(self) -> None:
                pass

        self.scraperStubClass = ScraperStub

        # When
        sut._scraperClasses.append(self.scraperStubClass)
        sut._scraperClasses.append(self.scraperStubClass)

        with self.assertRaises(LookupError):
            sut.makeFromScrapee(
                scrapee=scrapee,
                scrapeeRepo=Mock(),
                session=Mock(),
                requestClass=Mock,
                messenger=Mock())

    def test_makeFromScrapees(self):
        # Given
        url1 = "https://scrapee-1.com"
        url2 = "https://scrapee-2.com"

        class Scraper1(Scraper):
            URL: str = url1

            def run(self) -> None:
                pass

        class Scraper2(Scraper):
            URL: str = url2

            def run(self) -> None:
                pass

        sut = ScraperFactory()
        sut.register(class_=Scraper1)
        sut.register(class_=Scraper2)

        scrapee1 = Mock(spec_set=Scrapable)
        scrapee1.url = url1
        scrapee2 = Mock(spec_set=Scrapable)
        scrapee2.url = url2
        scrapees = [scrapee1, scrapee2]

        # When
        scrapers: List[Scraper] = sut.makeFromScrapees(
            scrapees=scrapees,
            scrapeeRepo=Mock(),
            session=Mock(),
            requestClass=Mock,
            messenger=Mock())

        # Then
        self.assertIsInstance(scrapers, list)
        self.assertEqual(2, len(scrapers))

    def test_makeFromScrapees_shouldReturnEmptyListWhenNoScrapeesGiven(self):
        # Given
        sut = ScraperFactory()

        # When
        scrapers: List[Scraper] = sut.makeFromScrapees(
            scrapees=[],
            scrapeeRepo=Mock(),
            session=Mock(),
            requestClass=Mock,
            messenger=Mock())

        # Then
        self.assertIsInstance(scrapers, list)
        self.assertEqual(0, len(scrapers))

    def test_makeFromScrapees_shouldReturnEmptyListWhenNoMatchingScrapers(self):
        # Given
        sut = ScraperFactory()
        scrapee = Mock(spec_set=Scrapable)
        scrapee.url = "https://should-lead-to-no-matching-scrapers.com"

        # When
        scrapers: List[Scraper] = sut.makeFromScrapees(
            scrapees=[scrapee],
            scrapeeRepo=Mock(),
            session=Mock(),
            requestClass=Mock,
            messenger=Mock())

        # Then
        self.assertIsInstance(scrapers, list)
        self.assertEqual(0, len(scrapers))