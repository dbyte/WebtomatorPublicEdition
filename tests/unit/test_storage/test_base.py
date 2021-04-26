# unit.test_storage.test_base.py
import pathlib as pl
import uuid
from unittest import mock
from unittest.mock import PropertyMock

from fixtures.storage import ConnectionImplFixture
from storage.base import PathCheckMode, Connection, Connectible, Dao, Identifiable
from unit.testhelper import WebtomatorTestCase


class PathCheckModeTest(WebtomatorTestCase):

    def test_ifWeKnowAllEnumCases(self):
        # Given
        sut = PathCheckMode
        expectedCases = 2

        # When
        actual = sut.__len__()

        # Then
        self.assertEqual(
            expectedCases, actual,
            f"Enum {sut.__name__}: Found {actual} cases, expected"
            f" {expectedCases} cases. Check/extend all test cases for this Enum.")

    def test_ifEnumValuesAreCorrect(self):
        # Given
        sut = PathCheckMode

        def errorMsg(a, b) -> str:
            return f"Enum case test result is {a}, but expected {b}"

        # When / Then
        actual = sut.File.value
        expected = 1
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.Directory.value
        expected = 2
        self.assertEqual(expected, actual, errorMsg(actual, expected))


class ConnectionTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.sut = ConnectionImplFixture()

    def tearDown(self) -> None:
        del self.sut

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Connection

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'db')
        self.assertHasAttribute(sut, 'path')
        self.assertHasAttribute(sut, 'open')
        self.assertHasAttribute(sut, 'close')
        self.assertHasAttribute(sut, 'isOpen')
        self.assertHasAttribute(sut, 'raiseWhenDisconnected')
        self.assertHasAttribute(sut, 'verifyPath')

    def test_raiseWhenDisconnected_shouldRaiseConnectionError(self):
        # Given
        self.sut.db = None

        # When / Then
        with self.assertRaises(ConnectionError):
            self.sut.raiseWhenDisconnected()

    def test_raiseWhenDisconnected_shouldNotRaiseConnectionError(self):
        # Given
        self.sut = ConnectionImplFixture()
        self.sut.db = "SomeDB-Reference-Stub"

        # When
        try:
            self.sut.raiseWhenDisconnected()

        # Then
        except Exception as e:
            self.fail(f"Expected no raise. But raised {e}")

    def test_raiseWhenDisconnected_shouldCallIsOpen(self):
        # When
        with mock.patch("storage.base.Connection.isOpen", new_callable=PropertyMock) as isOpen:
            self.sut.raiseWhenDisconnected()
            isOpen.assert_called_once()

    def test_verifyPath_shouldRaiseOnNoneOrEmptyPath(self):
        # Given
        self.sut.path = None
        # When / Then
        with self.assertRaises(ValueError):
            self.sut.verifyPath(PathCheckMode.File)

        # Given
        self.sut.path = pl.Path("")
        # When / Then
        with self.assertRaises(ValueError):
            self.sut.verifyPath(PathCheckMode.File)

    def test_verifyPath_shouldRaiseFileNotFoundError(self):
        # Given
        self.sut.path = pl.Path("Not/a/valid/file.txt")
        # When / Then
        with self.assertRaises(FileNotFoundError):
            self.sut.verifyPath(PathCheckMode.File)

    def test_verifyPath_shouldRaiseNotADirectoryError(self):
        # Given
        self.sut.path = pl.Path("Not/a/valid/directory/")
        # When / Then
        with self.assertRaises(NotADirectoryError):
            self.sut.verifyPath(PathCheckMode.Directory)

    def test_verifyPath_shouldRaiseNotImplementedError(self):
        # When / Then
        with self.assertRaises(NotImplementedError):
            # noinspection PyTypeChecker
            self.sut.verifyPath(mode="invalidMode")


class IdentifiableTest(WebtomatorTestCase):

    class IdentifiableTestImpl(Identifiable):
        def __init__(self):
            self.__uid: str = ""

        @property
        def uid(self) -> str:
            return self.__uid

        @uid.setter
        def uid(self, val: str) -> None:
            self.__uid = val

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Identifiable

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'uid')
        self.assertHasAttribute(sut, 'generateUID')

    def test_uid_shouldGetAndSet(self):
        # Given
        sut: Identifiable = self.IdentifiableTestImpl()
        givenInput = "708069a1-3475-48bb-8c8d-b647774f671c"

        # When
        sut.uid = givenInput

        # Then
        self.assertEqual(givenInput, sut.uid)

    def test_generateID(self):
        # Given
        sut: Identifiable = self.IdentifiableTestImpl()

        # When
        strUUID4 = sut.generateUID()

        # Then
        # Expect that the string is a UUIDv4
        try:
            uuid.UUID(strUUID4, version=4)

        except Exception as e:
            self.fail(f"Expected String '{strUUID4}' to carry a valid UUID4. "
                      f"Could not convert string to UUID4. Error: {e}")


class ConnectibleTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Connectible

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'connection')


class DaoTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Dao

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'loadAll')
        self.assertHasAttribute(sut, 'saveAll')
        self.assertHasAttribute(sut, 'deleteAll')
        self.assertHasAttribute(sut, 'insert')
        self.assertHasAttribute(sut, 'update')
