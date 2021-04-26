# unit.test_network.test_userAgentRepo.py
from unittest.mock import Mock

from network.userAgentDao import FileUserAgentDao
from network.userAgentRepo import UserAgentRepo
from fixtures.network import TEST_USERAGENTS_0VALID_REPO_PATH
from fixtures.network import TEST_USERAGENTS_TEMP_REPO_PATH, TEST_USERAGENTS_3VALID_REPO_PATH
from unit.testhelper import WebtomatorTestCase


class UserAgentRepoTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.tempUserAgentsRepoPath = TEST_USERAGENTS_TEMP_REPO_PATH
        if self.tempUserAgentsRepoPath.is_file():
            self.tempUserAgentsRepoPath.unlink()

    def tearDown(self) -> None:
        if self.tempUserAgentsRepoPath.is_file():
            self.tempUserAgentsRepoPath.unlink()
        del self.tempUserAgentsRepoPath

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = UserAgentRepo

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getAll')
        self.assertHasAttribute(sut, 'getRandomUserAgent')

    def test_init_shouldSetDefaultValues(self):
        # When
        daoMock = Mock()
        daoMock.myValue = "DAO Mock checkValue"
        sut = UserAgentRepo(dao=daoMock)

        # Then
        self.assertEqual("DAO Mock checkValue", sut._dao.myValue)

    def test_getRandomUserAgent(self):
        # Given
        testfileUserAgentDao = FileUserAgentDao(filepath=TEST_USERAGENTS_3VALID_REPO_PATH)
        sut = UserAgentRepo(dao=testfileUserAgentDao)

        expectedMinimumDifferentAgents = 3

        # When
        returnedAgents = []
        for i in range(1, 20):
            userAgent = sut.getRandomUserAgent()
            if userAgent not in returnedAgents:
                returnedAgents.append(userAgent)
            if len(returnedAgents) == expectedMinimumDifferentAgents:
                break

        # Then
        self.assertEqual(expectedMinimumDifferentAgents, len(returnedAgents),
                         f"Expected minimum {expectedMinimumDifferentAgents} different agents "
                         f"in 20 calls but got {len(returnedAgents)}")

    def test_getRandomUserAgent_shouldReturnNoneIfRepoIsEmpty(self):
        # Given
        testfileUserAgentDao = FileUserAgentDao(filepath=TEST_USERAGENTS_0VALID_REPO_PATH)
        sut = UserAgentRepo(dao=testfileUserAgentDao)

        # When
        userAgent = sut.getRandomUserAgent()

        # Then
        self.assertIsNone(userAgent, f"Got value {userAgent}")
