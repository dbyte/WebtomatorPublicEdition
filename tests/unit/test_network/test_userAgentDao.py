# unit.test_network.test_userAgentDao.py
from pathlib import Path
from typing import List

import fixtures.network
from network.userAgentDao import FileUserAgentDao
from unit.testhelper import WebtomatorTestCase


class UserAgentDaoTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.tempUserAgentsRepoPath = fixtures.network.TEST_USERAGENTS_TEMP_REPO_PATH
        if self.tempUserAgentsRepoPath.is_file():
            self.tempUserAgentsRepoPath.unlink()

    def tearDown(self) -> None:
        if self.tempUserAgentsRepoPath.is_file():
            self.tempUserAgentsRepoPath.unlink()
        del self.tempUserAgentsRepoPath

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = FileUserAgentDao

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'loadAll')
        self.assertHasAttribute(sut, 'insert')

    def test_init_shouldSetValidPath(self):
        # Given
        validPath = self.tempUserAgentsRepoPath

        # When
        sut = FileUserAgentDao(validPath)

        # Then
        self.assertEqual(validPath, sut.connection.path)

    def test_init_shouldSetDefaultPathIfNoneIsGiven(self):
        # When
        sut = FileUserAgentDao()

        # Then
        self.assertIn(str(Path("/userdata/")), str(sut.connection.path))

    def test_loadAll_shouldNotRaiseOnEmptyFile(self):
        # Given
        path = self.tempUserAgentsRepoPath
        path.touch()
        assert path.is_file()

        with FileUserAgentDao(path) as sut:
            # When
            try:
                sut.loadAll()

            # Then
            except Exception as e:
                self.fail(f"Expected no raise, but raised: {e}")

    def test_loadAll_shouldNotRaiseIfFileIsNotEmptyButAllLinesAreInvalid(self):
        # Given
        path = Path(fixtures.network.TEST_USERAGENTS_0VALID_REPO_PATH)

        with FileUserAgentDao(path) as sut:
            # When
            try:
                sut.loadAll()

            # Then
            except Exception as e:
                self.fail(f"Expected no raise, but raised: {e}")

    def test_loadAll_shouldFilterDisabledUserAgents(self):
        # Given
        path = Path(fixtures.network.TEST_USERAGENTS_3VALID_REPO_PATH)
        expectedData = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, "
            "like Gecko) Version/9.0.2 Safari/601.3.9)",

            "Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/51.0.2704.64 Safari/537.36)",

            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/47.0.2526.111 Safari/537.36)"
        ]

        # When
        with FileUserAgentDao(path) as sut:
            userAgents: List[str] = sut.loadAll()

        # Then
        self.assertIsInstance(userAgents, list)
        self.assertEqual(3, len(userAgents))
        self.assertEqual(set(expectedData), set(userAgents))

    def test_insert_shouldStripDuplicates(self):
        path = self.tempUserAgentsRepoPath

        # Write existing valid user agent before testing insert.
        existingAgent = "UserAgent 01 already exists in DB\n"
        with open(str(path), "w", encoding="utf-8") as file:
            file.write(existingAgent)

        # Data to be inserted
        agent2 = "UserAgent 02 should make its way into DB, but only once"
        agent3 = "UserAgent 03 is no duplicate and should be written to DB, too"

        with FileUserAgentDao(path) as sut:
            sut.insert(agent2)
            sut.insert(agent3)

            # When
            sut.insert(agent2)  # agent2 would be a duplicate should be stripped by DAO method

        # Then
        with open(str(path), "r", encoding="utf-8") as file:
            allSaved = [line.rstrip("\n") for line in file.readlines()]

        # We inserted 3, plus 1 already exists. 1 was a duplicate - so expect 3 instead of 4.
        self.assertEqual(3, len(allSaved))
        # Expect that all unique agents have been saved.
        self.assertIn("UserAgent 01 already exists in DB", allSaved)
        self.assertIn("UserAgent 02 should make its way into DB, but only once", allSaved)
        self.assertIn("UserAgent 03 is no duplicate and should be written to DB, too", allSaved)
