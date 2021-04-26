# unit.test_network.test_proxyRepo.py
from unittest.mock import Mock

from network.proxy import Proxy
from network.proxyDao import FileProxyDao
from network.proxyRepo import ProxyRepo
from fixtures.network import TEST_6VALID_PROXIES_REPO_PATH, TEST_0VALID_PROXIES_REPO_PATH
from fixtures.network import TEST_TEMP_PROXIES_REPO_PATH
from unit.testhelper import WebtomatorTestCase


class ProxyRepoTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.tempProxyRepoPath = TEST_TEMP_PROXIES_REPO_PATH
        if self.tempProxyRepoPath.is_file():
            self.tempProxyRepoPath.unlink()

    def tearDown(self) -> None:
        if self.tempProxyRepoPath.is_file():
            self.tempProxyRepoPath.unlink()
        del self.tempProxyRepoPath

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = ProxyRepo

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getAll')
        self.assertHasAttribute(sut, 'addProxy')
        self.assertHasAttribute(sut, 'getRandomProxy')

    def test_init_shouldSetDefaultValues(self):
        # When
        daoMock = Mock()
        daoMock.myValue = "DAO Mock checkValue"
        sut = ProxyRepo(dao=daoMock)

        # Then
        self.assertEqual("DAO Mock checkValue", sut._dao.myValue)

    def test_addProxy(self):
        # Given
        testfileProxyDao = FileProxyDao(filepath=self.tempProxyRepoPath)
        sut = ProxyRepo(dao=testfileProxyDao)

        proxy1 = Proxy.make(endpoint="this.is.valid",
                            port=9384,
                            username="SomeUsername",
                            pw="AndAPassword"
                            )
        proxy2 = Proxy.make(endpoint="a.better.world.for.com",
                            port=2837,
                            username="Myself",
                            pw="GreatPassword"
                            )
        # When
        sut.addProxy(proxy1)
        sut.addProxy(proxy2)

        # Then
        with open(str(self.tempProxyRepoPath), encoding="utf-8") as file:
            lines = [line.rstrip("\n") for line in file.readlines()]

        self.assertIsInstance(lines, list)
        self.assertEqual(2, len(lines))
        self.assertEqual("this.is.valid:9384:SomeUsername:AndAPassword", lines[0])
        self.assertEqual("a.better.world.for.com:2837:Myself:GreatPassword", lines[1])

    def test_addProxy_shouldRaiseOnInvalidProxy(self):
        # Given
        testfileProxyDao = FileProxyDao(filepath=self.tempProxyRepoPath)
        sut = ProxyRepo(dao=testfileProxyDao)

        proxy1 = Proxy.make(endpoint="Invalid endpoint, whitespace in string",
                            port=2938,
                            )

        # When / Then
        with self.assertRaises(ValueError):
            sut.addProxy(proxy1)

    def test_getRandomProxy(self):
        # Given
        testfileProxyDao = FileProxyDao(filepath=TEST_6VALID_PROXIES_REPO_PATH)
        sut = ProxyRepo(dao=testfileProxyDao)

        expectedMinimumDifferentProxies = 4

        # When
        returnedProxies = []
        for i in range(1, 20):
            proxy = sut.getRandomProxy()
            if proxy not in returnedProxies:
                returnedProxies.append(proxy)
            if len(returnedProxies) == expectedMinimumDifferentProxies:
                break

        # Then
        self.assertEqual(expectedMinimumDifferentProxies, len(returnedProxies),
                         f"Expected minimum {expectedMinimumDifferentProxies} different proxies "
                         f"in 20 calls but got {len(returnedProxies)}")

    def test_getRandomProxy_shouldReturnNoneIfRepoIsEmpty(self):
        # Given
        testfileProxyDao = FileProxyDao(filepath=TEST_0VALID_PROXIES_REPO_PATH)
        sut = ProxyRepo(dao=testfileProxyDao)

        # When
        proxy = sut.getRandomProxy()

        # Then
        self.assertIsNone(proxy, f"Got value {proxy}")