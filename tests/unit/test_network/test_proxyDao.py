# unit.test_network.test_proxyDao.py
import typing as tp
from pathlib import Path
from unittest import mock

from network.proxy import Proxy
from network.proxyDao import FileProxyDao
from unit.testhelper import WebtomatorTestCase

import fixtures.network


class ProxyDaoTest(WebtomatorTestCase):
    PATH_TO_6_VALID_PROXIES: tp.ClassVar

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.PATH_TO_6_VALID_PROXIES = Path(fixtures.network.TEST_6VALID_PROXIES_REPO_PATH)

    @classmethod
    def tearDownClass(cls):
        del cls.PATH_TO_6_VALID_PROXIES
        super().tearDownClass()

    def setUp(self) -> None:
        self.tempProxyRepoPath = fixtures.network.TEST_TEMP_PROXIES_REPO_PATH
        if self.tempProxyRepoPath.is_file():
            self.tempProxyRepoPath.unlink()

    def tearDown(self) -> None:
        if self.tempProxyRepoPath.is_file():
            self.tempProxyRepoPath.unlink()
        del self.tempProxyRepoPath

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = FileProxyDao

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'loadAll')
        self.assertHasAttribute(sut, 'insert')

    def test_init_shouldSetValidPath(self):
        # Given
        validPath = self.PATH_TO_6_VALID_PROXIES

        # When
        sut = FileProxyDao(validPath)

        # Then
        self.assertEqual(validPath, sut.connection.path)

    def test_init_shouldSetDefaultPathIfNoneIsGiven(self):
        # When
        sut = FileProxyDao()

        # Then
        self.assertIn(str(Path("/userdata/")), str(sut.connection.path))

    def test_contextManager(self):
        # Given
        path = fixtures.network.TEST_6VALID_PROXIES_REPO_PATH

        # When
        with FileProxyDao(path) as fileProxyDao:
            proxies = fileProxyDao.loadAll()

        # Then
        self.assertIsInstance(proxies, list)
        self.assertEqual(6, len(proxies))

    def test_loadAll_shouldNotRaiseOnValidRepoFile(self):
        with FileProxyDao(self.PATH_TO_6_VALID_PROXIES) as sut:
            # When
            try:
                sut.loadAll()

            # Then
            except Exception as e:
                self.fail(f"Expected no raise, but raised: {e}")

    def test_loadAll_shouldNotRaiseOnEmptyFile(self):
        # Given
        path = Path(fixtures.network.TEST_EMPTYFILE_PROXIES_REPO_PATH)

        with FileProxyDao(path) as sut:
            # When
            try:
                sut.loadAll()

            # Then
            except Exception as e:
                self.fail(f"Expected no raise, but raised: {e}")

    def test_loadAll_shouldNotRaiseIfFileIsNotEmptyButAllLinesAreInvalid(self):
        # Given
        path = Path(fixtures.network.TEST_0VALID_PROXIES_REPO_PATH)

        with FileProxyDao(path) as sut:
            # When
            try:
                sut.loadAll()

            # Then
            except Exception as e:
                self.fail(f"Expected no raise, but raised: {e}")

    def test_loadAll_shouldFilterDisabledProxies(self):
        # Given
        path = Path(fixtures.network.TEST_6VALID_PROXIES_REPO_PATH)

        # When
        with FileProxyDao(path) as sut:
            sut.loadAll()

        # Then
        self.assertEqual(6, len(sut._records.get(sut._recordArrayKey)))

    def test_loadAll_shouldFilterDuplicateProxies(self):
        # Given
        path = Path(fixtures.network.TEST_5WITH2DUPLICATES_PROXIES_REPO_PATH)

        # When
        with FileProxyDao(path) as sut:
            sut.loadAll()

        # Then
        self.assertEqual(3, len(sut._records.get(sut._recordArrayKey)))

    def test_insert(self):
        path = self.tempProxyRepoPath

        # Write some existing valid proxies before testing insert.
        existingProxies = [
            "243.172.183.94:8344:creepy-user:creepy_pass\n",
            "misoproponolpimpom:3344:jump-user:jump_pass"
        ]
        with open(str(path), "w", encoding="utf-8") as file:
            file.writelines(existingProxies)

        # Data to be inserted
        proxy1 = Proxy.make(endpoint="this.is.valid.com",
                            port=2938,
                            username="SomeUsername",
                            pw="AndAPassword"
                            )
        proxy2 = Proxy.make(endpoint="this.too.com",
                            port=8493,
                            username="Myself",
                            pw="GreatPassword"
                            )

        with FileProxyDao(path) as sut:
            # When
            sut.insert(proxy1)
            sut.insert(proxy2)

            # Then
            with open(str(path), encoding="utf-8") as file:
                lines = [line.rstrip("\n") for line in file.readlines()]

            self.assertIsInstance(lines, list)
            self.assertEqual(4, len(lines))
            self.assertEqual("243.172.183.94:8344:creepy-user:creepy_pass", lines[0])
            self.assertEqual("misoproponolpimpom:3344:jump-user:jump_pass", lines[1])
            self.assertEqual("this.is.valid.com:2938:SomeUsername:AndAPassword", lines[2])
            self.assertEqual("this.too.com:8493:Myself:GreatPassword", lines[3])

    def test_insert_shouldStripDuplicates(self):
        path = self.tempProxyRepoPath

        # Write existing valid proxy before testing insert.
        existingProxies = ["199.99.72.194:2837:creepy-user:creepy_pass\n"]
        with open(str(path), "w", encoding="utf-8") as file:
            file.writelines(existingProxies)

        # Data to be inserted
        proxy1 = Proxy.make(endpoint="this.is.valid.com",
                            port=2938,
                            username="SomeUsername",
                            pw="AndAPassword"
                            )
        proxy2 = Proxy.make(endpoint="this.too.com",
                            port=8493,
                            username="Myself",
                            pw="GreatPassword"
                            )

        with FileProxyDao(path) as sut:
            sut.insert(proxy1)
            sut.insert(proxy2)

            # When
            sut.insert(proxy1)  # proxy1 would be a duplicate should be stripped by DAO method

        # Then
        with open(str(path), "r", encoding="utf-8") as file:
            allSaved = [line.rstrip("\n") for line in file.readlines()]

        self.assertEqual(3, len(allSaved))
        self.assertIn("199.99.72.194:2837:creepy-user:creepy_pass", allSaved)
        self.assertIn("this.too.com:8493:Myself:GreatPassword", allSaved)
        self.assertIn("this.is.valid.com:2938:SomeUsername:AndAPassword", allSaved)

    def test_cleanupRecord_shouldBeCalled(self):
        path = Path(fixtures.network.TEST_EXACT3_PROXIES_REPO_PATH)

        # When
        with FileProxyDao(path) as sut:
            with mock.patch("network.proxyDao.FileProxyDao._cleanupRecord") as mockedMethod:
                mockedMethod.return_value = ""
                sut.loadAll()

        mockedMethod.assert_called()
        self.assertEqual(3, mockedMethod.call_count)

    def test_filterRecord_shouldBeCalled(self):
        path = Path(fixtures.network.TEST_EXACT3_PROXIES_REPO_PATH)

        # When
        with FileProxyDao(path) as sut:
            with mock.patch("network.proxyDao.FileProxyDao._filterRecord") as mockedMethod:
                mockedMethod.return_value = ""
                sut.loadAll()

        mockedMethod.assert_called()
        self.assertEqual(3, mockedMethod.call_count)

    def test_postprocess_shouldBeCalled(self):
        path = Path(fixtures.network.TEST_EXACT3_PROXIES_REPO_PATH)

        # When
        with FileProxyDao(path) as sut:
            with mock.patch("network.proxyDao.FileProxyDao._postprocess") as mockedMethod:
                mockedMethod.return_value = ""
                sut.loadAll()

        mockedMethod.assert_called_once()
