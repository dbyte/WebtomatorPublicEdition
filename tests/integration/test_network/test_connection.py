# integration.test_network.test_connection.py
import asyncio
from typing import List

import debug.logger as clog
from integration.testhelper import NetworkHelper, ProductsUrlsRepoMock
from network.connection import AioHttpRequest, AioHttpSession, Response
from unit.testhelper import WebtomatorTestCase, LogHelper


class AioHttpRequestTest(WebtomatorTestCase):
    netHelper: NetworkHelper
    productsUrlsRepoMock: ProductsUrlsRepoMock

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.netHelper = NetworkHelper()
        cls.productsUrlsRepoMock = ProductsUrlsRepoMock()
        # Show some logging while testing, esp. with custom time and sourcecode info
        LogHelper.activate(level=clog.INFO)

    @classmethod
    def tearDownClass(cls):
        LogHelper.reset()
        del cls.netHelper, cls.productsUrlsRepoMock
        super().tearDownClass()

    def test_fetch_withReliableSites(self):
        # Given
        urls = [
            "http://www.rsebe.de", "https://filemaker-magazin.de",
            "https://www.studienkreis.de/"
        ]

        # When
        clientResponses: List[Response] = asyncio.run(self._fetchRunner(urls, timeout=7))

        # Then
        self.assertIsInstance(clientResponses, list)
        self.assertEqual(3, len(clientResponses))
        for response in clientResponses:
            if response.error:
                self.fail(f"Expected success for all URLs, got error: {repr(response.error)}")

            self.assertIsNotNone(response, f"Response object is None.")
            self.assertIsNotNone(response.data, f"Response.data object is None.")
            self.assertEqual(200, response.data.status)

    def test_fetch_withRealProductSites(self):
        # Given
        realURLs = self.productsUrlsRepoMock.getAllUrls()

        # When
        clientResponses: List[Response] = asyncio.run(self._fetchRunner(realURLs, timeout=7))

        # Then
        self.assertIsInstance(clientResponses, list)
        for response in clientResponses:
            self.assertIsNotNone(response, f"Response object is None.")
            self.assertIsNotNone(response.data, f"Response data is None for {response}")
            # Just check for response status > 0, not for 200... too often it's 403 :-(
            self.assertGreater(response.data.status, 0, f"Response: {response.data}")

    async def _fetchRunner(self, urls: list, timeout: int) -> List[Response]:
        # Init a persistent session for all requests
        session = AioHttpSession(
            proxyRepo=self.netHelper.proxyRepo,
            userAgentRepo=self.netHelper.userAgentRepo)

        sut = AioHttpRequest(session=session)
        sut.configure(maxRetries=4, timeout=timeout, useRandomProxy=True)

        tasks = [self._fetchData(sut, url, timeout) for url in urls]
        responses: List[Response] = await asyncio.gather(*tasks)

        # Do not forget to close session...
        await session.close()

        return responses

    @staticmethod
    async def _fetchData(sut: AioHttpRequest, url: str, timeout: int):
        """ Test-helper method
        """
        result = ""
        fetchParams = sut.Params(url=url)
        response: Response = await sut.fetch(params=fetchParams)
        if response.error:
            result = "Response is None."
            result += f"\nError object: {repr(response.error)}"
        elif response.data:
            result = str(response.data.status)
            result += f"\n✅ Content text exists: {response.text is not None}"
            result += f"\n✅ Error object is None"

        print("-" * 60, f"{url}", result, "-" * 60, sep="\n")
        print()

        return response