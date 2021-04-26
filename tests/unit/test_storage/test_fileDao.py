# unit.storage.test_fileDao.py
import json
import pathlib as pl
from typing import IO, List
from unittest import mock
from unittest.mock import Mock

from fixtures.storage import STORAGE_TEST_PATH
from storage.base import PathCheckMode
from storage.fileDao import FileConnection, FileDao, TextFileDao, JsonFileDao
from unit.testhelper import WebtomatorTestCase


def _fileDaoConnectionPatch() -> mock._patch:
    connectionPatch = mock.patch("storage.fileDao.FileDao.connection", set_spec=FileConnection)
    connectionPatch.db = Mock(spec=IO)
    return connectionPatch


def _fileDaoBuiltinOpenPatch() -> mock._patch:
    openPatch = mock.patch("storage.fileDao.open")
    return openPatch


def _fileDaoLoadAllPatch() -> mock._patch:
    loadAllPatch = mock.patch("storage.fileDao.FileDao.loadAll", autospec=True)
    return loadAllPatch


class FileConnectionTest(WebtomatorTestCase):
    # No files / no dirs will be created physically during tests.
    # This is just a dummy path.
    testDir = pl.Path("This is a fake path/no file.txt")

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = FileConnection

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'db')
        self.assertHasAttribute(sut, 'path')
        self.assertHasAttribute(sut, 'open')
        self.assertHasAttribute(sut, 'close')

    def test_open_shouldCallBuiltinOpenWithCorrectArguments(self):
        # Given
        filename = "test_open_shouldCallBuiltinOpenWithCorrectArguments.txt"
        sut = FileConnection(self.testDir / filename)

        builtinOpenPatch = _fileDaoBuiltinOpenPatch()
        builtinOpenMock = builtinOpenPatch.start()

        # When
        sut.open()

        builtinOpenPatch.stop()

        # Then
        builtinOpenMock.assert_called_with(str(self.testDir / filename), "a+", encoding="utf-8")

    def test_open_shouldSetDbProperty(self):
        # Given
        filename = "test_open_shouldSetDbProperty.txt"
        sut = FileConnection(self.testDir / filename)

        builtinOpenPatch = _fileDaoBuiltinOpenPatch()
        builtinOpenMock = builtinOpenPatch.start()
        builtinOpenMock.return_value = "referenceDummy"

        # When
        sut.open()

        builtinOpenPatch.stop()

        # Then
        self.assertEqual(sut.db, "referenceDummy")

    def test_open_shouldRaiseOnFailedBuiltinFileOpen(self):
        # Given
        filename = "test_open_shouldRaiseOnFailedBuiltinFileOpen.txt"
        sut = FileConnection(self.testDir / filename)

        # When
        builtinOpenPatch = _fileDaoBuiltinOpenPatch()
        builtinOpenMock = builtinOpenPatch.start()
        builtinOpenMock.side_effect = IOError

        # Then
        with self.assertRaises(IOError):
            sut.open()

        builtinOpenPatch.stop()

    def test_close_shouldCallBuiltinFileClose(self):
        # Given
        filename = "test_close_shouldCallBuiltinFileClose.txt"
        sut = FileConnection(self.testDir / filename)

        builtinOpenPatch = _fileDaoBuiltinOpenPatch()
        builtinOpenPatch.start()
        sut.open()
        self.assertIsNotNone(sut.db)  # precondition for the test

        with mock.patch("storage.fileDao.FileConnection.db",
                        return_value=Mock(),
                        create=True) as mockDb:
            sut.close()

        # Then
        mockDb.close.assert_called_once()

        builtinOpenPatch.stop()

    def test_close_shouldSetDbPropertyToNone(self):
        # Given
        filename = "test_close_shouldSetDbPropertyToNone.txt"
        sut = FileConnection(self.testDir / filename)

        builtinOpenPatch = _fileDaoBuiltinOpenPatch()
        builtinOpenPatch.start()

        sut.open()
        self.assertIsNotNone(sut.db)  # precondition for the test

        # When
        sut.close()

        # Then
        self.assertIsNone(sut.db)

        builtinOpenPatch.stop()


class FileDaoTest(WebtomatorTestCase):
    # Need to stub an implementation since FileDao is an Interface which itself is inherited
    # from Interface 'Dao' and does not completely satisfy all properties of 'Dao'.
    # If some of that missing properties are going to be implemented in FileDao in the future,
    # we need to remove it from the test impl - otherwise some tests will fail.
    class FileDaoTestImpl(FileDao):
        def insert(self, data):
            raise NotImplementedError

        def update(self, data):
            raise NotImplementedError

        def find(self, **kwargs):
            raise NotImplementedError

    testDir = STORAGE_TEST_PATH

    def setUp(self) -> None:
        self.fullPath = pl.Path("")

    def tearDown(self) -> None:
        self.deleteTestfile()
        del self.fullPath

    def deleteTestfile(self):
        if self.fullPath.is_file():
            self.fullPath.unlink()

    def test_loadAll_shouldCallExpectedMethods(self):
        # Given
        sut: FileDao = self.FileDaoTestImpl(self.testDir)

        # When
        with mock.patch(
                "storage.fileDao.FileDao.connection", set_spec=FileConnection) as connectionMock:
            sut.loadAll()

        # Then
        # Expected calls. We also check the order of calls.
        expectedCalls = [
            mock.call.raiseWhenDisconnected(),
            mock.call.verifyPath(PathCheckMode.File),
            mock.call.db.seek(0)
        ]
        connectionMock.assert_has_calls(any_order=False, calls=expectedCalls)

    def test_loadAll_shouldRaiseWhenDisconnected(self):
        # Given
        sut: FileDao = \
            self.FileDaoTestImpl(self.testDir / "test_loadAll_shouldRaiseWhenDisconnected.txt")
        sut.connection.close()

        # When / Then
        with self.assertRaises(ConnectionError):
            sut.loadAll()

    def test_loadAll_shouldRaiseOnInvalidParentPath(self):
        # Given
        sut: FileDao = self.FileDaoTestImpl(pl.Path("Invalid/directory") /
                                            "test_loadAll_shouldRaiseOnInvalidParentPath.txt")
        # When / Then
        # Expect FileNotFoundError on invalid parent dir
        with self.assertRaises(FileNotFoundError):
            sut.connection.open()
            sut.loadAll()
            sut.connection.close()

    def test_loadAll_shouldLoadExistingFile(self):
        # Given
        self.fullPath = self.testDir / "test_loadAll_shouldLoadExistingFile.txt"
        sut: FileDao = self.FileDaoTestImpl(self.fullPath)
        expectedData = "Some data right here."

        # Generate file, since we need to test for an existing file
        with open(str(self.fullPath), "w+", encoding="utf-8") as file:
            file.write(expectedData)
        # Precondition for testing
        self.assertTrue(self.fullPath.is_file())

        # When
        sut.connection.open()
        sut.loadAll()

        # Then
        loadedData = sut.connection.db.read()
        # Expect that all data can immediately be read
        self.assertEqual(expectedData, loadedData)

        sut.connection.close()

    def test_loadAll_shouldCreateNewFileAtValidGivenPath(self):
        # Given
        self.fullPath = self.testDir / "test_loadAll_shouldCreateNewFileAtValidGivenPath.txt"
        sut: FileDao = self.FileDaoTestImpl(self.fullPath)

        # When
        sut.connection.open()
        sut.loadAll()

        # Then
        # Expect that file was created at given path
        self.assertTrue(self.fullPath.is_file(), "Expected that file was created but not created.")
        # Expect that file is empty
        loadedData = sut.connection.db.read()
        self.assertEqual("", loadedData)

        sut.connection.close()

    def test_saveAll_shouldWriteDataToNewFile(self):
        # Given
        self.fullPath = self.testDir / "test_saveAll_shouldWriteDataToFile.txt"
        expectedData = "Test text content öäü €"

        # When
        with self.FileDaoTestImpl(self.fullPath) as sut:
            sut.saveAll(expectedData)

        # Then
        with open(str(self.fullPath), encoding="utf-8") as file:
            savedContent = file.read()
            self.assertEqual(expectedData, savedContent)

    def test_saveAll_shouldOverwriteDataOfExistingFile(self):
        # Given
        self.fullPath = self.testDir / "test_saveAll_shouldOverwriteDataOfExistingFile.txt"
        dataToDelete = "This is some content which should be implicitly deleted."

        # When
        # First, make a new File and set some data
        sut: FileDao = self.FileDaoTestImpl(self.fullPath)
        sut.connection.open()
        sut.saveAll(dataToDelete)
        # As a precondition for the test, check if content was written to file.
        self.assertEqual(dataToDelete, sut.connection.db.read())

        # Now call save again - should overwrite all content with new data
        newData = "This is new data which should replace all existing content of the file."
        sut.saveAll(newData)
        sut.connection.close()

        # Then
        with open(str(self.fullPath), encoding="utf-8") as file:
            savedContent = file.read()
            self.assertEqual(newData, savedContent)

    def test_saveAll_shouldRaiseWhenDisconnected(self):
        # Given
        sut: FileDao = self.FileDaoTestImpl(self.testDir / "test_saveAll_shouldRaiseWhenDisconnected.txt")
        sut.connection.close()

        # When / Then
        with self.assertRaises(ConnectionError):
            sut.saveAll()

    def test_saveAll_shouldCallPrecheckingMethods(self):
        # Given
        sut: FileDao = self.FileDaoTestImpl(self.testDir)

        fileDaoConnectionPatch = _fileDaoConnectionPatch()
        fileDaoConnectionMock = fileDaoConnectionPatch.start()

        # When
        sut.saveAll()

        # Then
        # Expected calls. We also check the order of calls.
        expectedCalls = [
            mock.call.raiseWhenDisconnected(),
            mock.call.verifyPath(PathCheckMode.Directory)
        ]
        fileDaoConnectionMock.assert_has_calls(any_order=False, calls=expectedCalls)

        fileDaoConnectionPatch.stop()

    def test_deleteAll_shouldDeleteAllContentOfFile(self):
        # Given
        self.fullPath = self.testDir / "test_deleteAll_shouldDeleteAllContentOfFile.txt"
        dataToDelete = "This is some content which should be deleted."

        # First, make a new File and set some data
        sut: FileDao = self.FileDaoTestImpl(self.fullPath)
        sut.connection.open()
        sut.saveAll(dataToDelete)
        # As a precondition for the test, check if content was written to file.
        self.assertEqual(dataToDelete, sut.connection.db.read())

        # When
        sut.deleteAll()
        sut.connection.close()

        # Then
        with open(str(self.fullPath), encoding="utf-8") as file:
            savedContent = file.read()
            self.assertEqual("", savedContent)

    def test_deleteAll_shouldCallPrecheckingMethods(self):
        # Given
        sut: FileDao = self.FileDaoTestImpl(self.testDir)

        fileDaoConnectionPatch = _fileDaoConnectionPatch()
        fileDaoConnectionMock = fileDaoConnectionPatch.start()

        # When
        sut.deleteAll()

        # Then
        # Expected calls. We also check the order of calls.
        expectedCalls = [
            mock.call.raiseWhenDisconnected(),
            mock.call.verifyPath(PathCheckMode.File)
        ]
        fileDaoConnectionMock.assert_has_calls(any_order=False, calls=expectedCalls)

        fileDaoConnectionPatch.stop()


class TextFileDaoTest(WebtomatorTestCase):
    # Need to stub an implementation since TextFileDao is an Interface which itself is
    # inherited from Interface 'Dao' and does not completely satisfy all properties of 'Dao'.
    # If some of that missing properties are going to be implemented in TextFileDao
    # in the future, we need to remove it from the test impl - otherwise some tests will fail.
    class TextFileDaoTestImpl(TextFileDao):

        def update(self, data):
            raise NotImplementedError

        def find(self, **kwargs):
            raise NotImplementedError

    testDir = STORAGE_TEST_PATH

    def setUp(self) -> None:
        self.fullPath = pl.Path("")

    def tearDown(self) -> None:
        self.deleteTestfile()
        del self.fullPath

    def deleteTestfile(self):
        if self.fullPath.is_file():
            self.fullPath.unlink()

    def test_init_shouldSetCorrectProperties(self):
        # When
        sut = self.TextFileDaoTestImpl(self.testDir)

        # Then
        self.assertEqual("data", sut._recordArrayKey)
        self.assertEqual(None, sut._records)

    def test_loadAll_shouldCallSuperLoadAll(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")

        fileDaoLoadAllPatch = _fileDaoLoadAllPatch()
        superLoadAllMock = fileDaoLoadAllPatch.start()

        fileDaoConnectionPatch = _fileDaoConnectionPatch()
        fileDaoConnectionPatch.start()

        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            # When
            sut.loadAll()

        # Then
        superLoadAllMock.assert_called_with(sut)

        fileDaoLoadAllPatch.stop()
        fileDaoConnectionPatch.stop()

    def test_loadAll_shouldReturnRecordsDict(self):
        # Given
        self.fullPath = pl.Path("no/path")

        givenLines = [
            "this is the first line",
            "this line is the second",
            "these are some special chars: öäü @  | € $ ß"
        ]

        self._startPatchesForExtendedLoadAllTests(givenLines)

        # When
        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            resultDict = sut.loadAll()

        # Then
        # Expect that result is a dict
        self.assertIsInstance(resultDict, dict)
        # Expect that the dict's default root key is "data"
        self.assertIn("data", resultDict.keys())
        # Expect we got identical list data
        self.assertListEqual(givenLines, resultDict.get("data"))

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldRemoveNewlineChars(self):
        # Given
        self.fullPath = pl.Path("no/path")

        givenLines = [
            "This is the first line with \n a new line char.",
            "A second line with carriage return char \r which should be removed, too.",
            "And a third line with both \r\n which should also be removed."
        ]

        expectedLines = [
            "This is the first line with  a new line char.",
            "A second line with carriage return char  which should be removed, too.",
            "And a third line with both  which should also be removed."
        ]

        self._startPatchesForExtendedLoadAllTests(givenLines)

        # When
        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            resultDict = sut.loadAll()

        # Then
        # Expect we got identical list data
        self.assertListEqual(expectedLines, resultDict.get("data"))

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldReturnDataWithCustomRootKeyWhenGiven(self):
        # Given
        self.fullPath = pl.Path("no/path")
        expectedLines = ["Unimportant dummy data here."]

        self._startPatchesForExtendedLoadAllTests(expectedLines)

        # When
        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            sut._recordArrayKey = "CustomRootKey"
            resultDict = sut.loadAll()

        # Then
        # Expect we got the list data by the custom root key
        self.assertListEqual(expectedLines, resultDict.get("CustomRootKey"))

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldStripDuplicates(self):
        # Given
        self.fullPath = self.testDir / "test_loadAll_shouldStripDuplicates.txt"
        preparedSUT: FileDao = self.TextFileDaoTestImpl(self.fullPath)
        # Prepare file with some duplicate data
        expectedData: List[str] = self._createFixtureForDuplicateTests(self.fullPath)

        # When
        with preparedSUT as sut:
            loadedData = sut.loadAll()

        # Then
        self.assertIsInstance(loadedData, dict)
        # Expect that dict has a list of records
        records = loadedData.get(sut._recordArrayKey, None)
        self.assertIsInstance(records, list)
        # Expect that only 5 records have been loaded (meaning no duplicates have been loaded)
        self.assertEqual(5, len(records))
        # Expect that all unique values have been loaded (do not check order)
        self.assertEqual(set(expectedData), set(records))

    def test_saveAll(self):
        # Given
        self.fullPath = self.testDir / "test_saveAll.txt"
        preparedSUT: FileDao = self.TextFileDaoTestImpl(self.fullPath)
        # Prepare file with some data
        expectedData: List[str] = self._createFixtureForDuplicateTests(self.fullPath)
        dataStr = "\n".join(expectedData)

        # When
        with preparedSUT as sut:
            sut.saveAll(data=dataStr)

        # Then
        with open(str(self.fullPath), encoding="utf-8") as file:
            allData = [line.rstrip("\n") for line in file.readlines()]

        self.assertEqual(set(expectedData), set(allData))

    def test_saveAll_shouldRaiseOnEmptyData(self):
        # Given
        self.fullPath = self.testDir / "test_saveAll_shouldRaiseOnEmptyData.txt"
        preparedSUT: FileDao = self.TextFileDaoTestImpl(self.fullPath)
        emptyData = ""

        # When / Then
        with preparedSUT as sut:
            with self.assertRaises(ValueError):
                sut.saveAll(data=emptyData)

    def test_saveAll_shouldRaiseOnInvalidDataType(self):
        # Given
        self.fullPath = self.testDir / "test_saveAll_shouldRaiseOnInvalidDataType.txt"
        preparedSUT: FileDao = self.TextFileDaoTestImpl(self.fullPath)
        invalidData = 2  # Is int but should be str - so expect raise

        # When / Then
        with preparedSUT as sut:
            with self.assertRaises(TypeError):
                sut.saveAll(data=invalidData)

    def test_insert_shouldInsertIntoNewFile(self):
        # Given
        self.fullPath = pl.Path(self.testDir, f"{__class__.__name__}.test_insert.txt")
        expectedData = "This should be a new line öäü ?€ ® (record)"

        # When
        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            sut.insert(data=expectedData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            savedData = file.read()
        # Expect that data has been saved
        self.assertEqual(expectedData, savedData)

    def test_insert_shouldInsertIntoExistingData(self):
        # Given
        self.fullPath = pl.Path(self.testDir, f"{__class__.__name__}.test_insert.txt")
        expectedData = "This should be a new line öäü ?€ (record)"

        # Create a file and some example data which will be extended by the inserted data
        existingData = "One line\nSecond line\nThird line\n"
        with open(str(self.fullPath), "w+", encoding="utf-8") as file:
            file.write(existingData)
            file.seek(0)
            assert file.read() == existingData  # Precondition for the test

        # When
        with self.TextFileDaoTestImpl(self.fullPath) as sut:
            sut.insert(data=expectedData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            savedData = file.read()
        # Expect that data has been added to existing data
        self.assertEqual(existingData + expectedData, savedData)

    def test_insert_shouldStripDuplicates(self):
        # Given
        self.fullPath = pl.Path(self.testDir, f"{__class__.__name__}.test_insert.txt")
        preparedSUT: FileDao = self.TextFileDaoTestImpl(self.fullPath)
        # Prepare file with some duplicate data
        expectedData: List[str] = self._createFixtureForDuplicateTests(self.fullPath)
        assert isinstance(expectedData, list)
        duplicate1 = expectedData[1]  # duplicate of existing data
        duplicate2 = expectedData[2]  # dito

        # When
        with preparedSUT as sut:
            sut.insert(data=duplicate1)
            sut.insert(data=duplicate2)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            allData = [line.rstrip("\n") for line in file.readlines()]

        # Expect data from file
        self.assertIsInstance(allData, list)
        # Expect that all unique values have been loaded (do not check order)
        self.assertEqual(set(expectedData), set(allData))

    def _startPatchesForExtendedLoadAllTests(self, resultList: list):
        self.fileDaoLoadAllPatch = _fileDaoLoadAllPatch()
        self.fileDaoLoadAllPatch.start()

        self.fileDaoConnectionPatch = _fileDaoConnectionPatch()
        self.fileDaoConnectionMock = self.fileDaoConnectionPatch.start()
        self.fileDaoConnectionMock.db.readlines.return_value = resultList

    def _stopPatchesForExtendedLoadAllTests(self):
        self.fileDaoLoadAllPatch.stop()
        self.fileDaoConnectionPatch.stop()
        del self.fileDaoLoadAllPatch, self.fileDaoConnectionPatch
        del self.fileDaoConnectionMock

    @classmethod
    def _createFixtureForDuplicateTests(cls, path: pl.Path) -> List[str]:
        expectedData = ["one", "two", "three", "four", "five"]
        duplicateData = ["two", "four", "five"]

        # Write some data with duplicates before testing
        with open(str(path), "w+", encoding="utf-8") as file:
            asString = "\n".join(expectedData) + "\n" + "\n".join(duplicateData)
            file.write(asString)
            file.flush()
            file.seek(0)
            assert asString == file.read()  # Precondition for testing

        return expectedData


class JsonFileDaoTest(WebtomatorTestCase):
    # Need to stub an implementation since JsonFileDao is an Interface which itself is
    # inherited from Interface 'Dao' and does not completely satisfy all properties of 'Dao'.
    # If some of that missing properties are going to be implemented in JsonFileDao
    # in the future, we need to remove it from the test impl - otherwise some tests will fail.
    class JsonFileDaoTestImpl(JsonFileDao):

        def update(self, data):
            raise NotImplementedError

        def find(self, **kwargs):
            raise NotImplementedError

    testDir = STORAGE_TEST_PATH

    def setUp(self) -> None:
        self.fullPath = pl.Path("")

    def tearDown(self) -> None:
        self.deleteTestfile()
        del self.fullPath

    def deleteTestfile(self):
        if self.fullPath.is_file():
            self.fullPath.unlink()

    def test_loadAll_shouldCallSuperLoadAll(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        dataStr = json.dumps(dict(key01="value01"))

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            sut.loadAll()

        # Then
        self.fileDaoLoadAllMock.assert_called_with(sut)

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldReturnAllData(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")

        givenRecords = [{'key01': 'one'}, {'key02': 'two'}, {'key03': 'three'}]
        dataStr = json.dumps(givenRecords)

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            resultList = sut.loadAll()

        # Then
        self.assertListEqual(givenRecords, resultList)

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldReturnTableDataIfTableKeyIsGiven(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        table = "MyTableIdentifier"

        givenTableRecords = [{'key01': 'one'}, {'key02': 'two'}, {'key03': 'three'}]
        allData = {table: givenTableRecords}
        dataStr = json.dumps(allData)

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=table) as sut:
            resultList = sut.loadAll()

        # Then
        self.assertListEqual(givenTableRecords, resultList)

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldRaiseIfTableKeyIsGivenButNotFound(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        table = "MyTableIdentifier"
        dataStr = json.dumps(dict(key01="value01"))

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.assertRaises(KeyError):
            with self.JsonFileDaoTestImpl(path=self.fullPath, table=table) as sut:
                sut.loadAll()

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldRaiseOnInvalidJson(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        dataStr = "This is a plain string - hence an invalid JSON format."

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.assertRaises(ValueError):
            with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
                sut.loadAll()

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldRaiseOnOtherErrors(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        dataStr = None  # when data is nil
        # noinspection PyTypeChecker
        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        with self.assertRaises(Exception):
            with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
                sut.loadAll()

        self._stopPatchesForExtendedLoadAllTests()

    def test_loadAll_shouldNotRaiseOnEmptyJson(self):
        # Given
        self.fullPath = pl.Path("no/file.txt")
        dataStr = "{}"

        self._startPatchesForExtendedLoadAllTests(dataStr)

        # When / Then
        try:
            with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
                sut.loadAll()

        except Exception as e:
            self.fail(f"Expected no raise, but raised: {e}")

        self._stopPatchesForExtendedLoadAllTests()

    def test_saveAll_shouldCorrelateWithLoadAll_list(self):
        # Given
        self.fullPath = self.testDir / f"{__class__.__name__}.test_saveAll_list.json"
        givenList = [{'key01': 'one'}, {'key02': 'two'}, {'key03': 'three'}]

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            sut.saveAll(givenList)
            result = sut.loadAll()

        # Then
        self.assertListEqual(givenList, result)

    def test_saveAll_shouldCorrelateWithLoadAll_dict(self):
        # Given
        self.fullPath = self.testDir / f"{__class__.__name__}.test_saveAll_dict.json"
        givenDict = {'key01': {'key02': {'key03': 'three'}}}

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            sut.saveAll(givenDict)
            result = sut.loadAll()

        # Then
        self.assertDictEqual(givenDict, result)

    def test_saveAll_shouldRaiseOnInvalidDataType(self):
        # Given
        self.fullPath = self.testDir / "shouldNotBeSaved.json"
        dataWithInvalidType = "This is plain text, should be rejected."

        # When / Then
        with self.assertRaises(TypeError):
            with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
                sut.saveAll(dataWithInvalidType)

    def test_saveAll_shouldRaiseOnInvalidFilename(self):
        # Given
        data = {}

        # When / Then
        with self.assertRaises(ValueError):
            filePathWithInvalidSuffix = self.testDir / "invalid file suffix.xml"
            with self.JsonFileDaoTestImpl(path=filePathWithInvalidSuffix, table=None) as sut:
                sut.saveAll(data)

        if filePathWithInvalidSuffix.is_file():
            filePathWithInvalidSuffix.unlink()

        # When / Then
        with self.assertRaises((FileNotFoundError, ValueError)):
            filePathWithBackslash = self.testDir / "here we have a\\backslash.json"
            with self.JsonFileDaoTestImpl(path=filePathWithBackslash, table=None) as sut:
                sut.saveAll(data)

        if filePathWithBackslash.is_file():
            filePathWithBackslash.unlink()

        # When / Then
        with self.assertRaises(ValueError):
            filePathWithStartingDot = self.testDir / ".Filename starting with dot.json"
            with self.JsonFileDaoTestImpl(path=filePathWithStartingDot, table=None) as sut:
                sut.saveAll(data)

        if filePathWithStartingDot.is_file():
            filePathWithStartingDot.unlink()

    def test_insert_withoutTable(self):
        # Given
        self.fullPath = self.testDir / f"{__class__.__name__}.test_insert_withoutTable.json"
        someData = dict(someDataMaster=
                        dict(key01="Value for key01", key02="Another value for key02"))

        insertionData = dict(insertionMaster=
                             dict(key03="Insertion value for key03",
                                  key04="Another insertion value for key04"))

        # Persist some example data before testing.
        with open(str(self.fullPath), "w+", encoding="utf-8") as file:
            json.dump(someData, file)

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            sut.insert(data=insertionData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            dataAfterInsert = json.load(file)

        self.assertDictEqual(someData.get("someDataMaster"),
                             dataAfterInsert.get("someDataMaster"))

        self.assertDictEqual(insertionData.get("insertionMaster"),
                             dataAfterInsert.get("insertionMaster"))

    def test_insert_withoutTable_shouldWorkWithNewFile(self):
        # Given
        self.fullPath =\
            self.testDir / f"{__class__.__name__}.test_insert_shouldWorkWithNewFile.json"

        insertionData = dict(insertionMaster=
                             dict(key03="Insertion value for key03",
                                  key04="Another insertion value for key04"))

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=None) as sut:
            sut.insert(data=insertionData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            dataAfterInsert = json.load(file)

        self.assertDictEqual(insertionData.get("insertionMaster"),
                             dataAfterInsert.get("insertionMaster"))

    def test_insert_withTable_shouldWorkWithNewFile(self):
        # Given
        self.fullPath = \
            self.testDir / f"{__class__.__name__}.test_insert_shouldWorkWithNewFile.json"

        tableName = "RootTable"
        insertionData = dict(insertionMaster=
                             dict(key01="Insertion value for key01",
                                  key02="Another insertion value for key02"))

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=tableName) as sut:
            sut.insert(data=insertionData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            dataAfterInsert = json.load(file)

        self.assertIsNotNone(dataAfterInsert.get(tableName),
                             f"Expected table '{tableName}' not found in data.")

        self.assertDictEqual(insertionData.get("insertionMaster"),
                             dataAfterInsert.get(tableName).get("insertionMaster"))

    def test_insert_withTable(self):
        # Given
        self.fullPath = self.testDir / f"{__class__.__name__}.test_insert_withTable.json"
        tableName = "mainTable"
        mainTableData = dict(mainTable=
                             dict(key01="Value for key01", key02="Another value for key02"))

        insertionData = dict(insertionData=
                             dict(key03="Insertion value for key03",
                                  key04="Another insertion value for key04"))

        # Persist some example data with "mainTable" before testing.
        with open(str(self.fullPath), "w+", encoding="utf-8") as file:
            json.dump(mainTableData, file)

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath, table=tableName) as sut:
            sut.insert(data=insertionData)

        # Then
        with open(str(self.fullPath), "r", encoding="utf-8") as file:
            dataAfterInsert = json.load(file)

        savedTableData = dataAfterInsert.get("mainTable")
        self.assertEqual("Value for key01", savedTableData.get("key01"))
        self.assertEqual("Another value for key02", savedTableData.get("key02"))

        savedInsertionData = savedTableData.get("insertionData")
        self.assertEqual("Insertion value for key03", savedInsertionData.get("key03"))
        self.assertEqual("Another insertion value for key04", savedInsertionData.get("key04"))

    def test_insert_shouldRaiseIfGivenDataHasInvalidType(self):
        # Given
        self.fullPath = self.testDir / f"{__class__.__name__}.test_insert_shouldRaise.json"
        invalidData = Mock(name="invalid data type")

        # When
        with self.JsonFileDaoTestImpl(path=self.fullPath) as sut:
            with self.assertRaises(TypeError):
                sut.insert(data=invalidData)

    def _startPatchesForExtendedLoadAllTests(self, jsonString: str):
        self.fileDaoLoadAllPatch = _fileDaoLoadAllPatch()
        self.fileDaoLoadAllMock = self.fileDaoLoadAllPatch.start()

        self.fileDaoConnectionPatch = _fileDaoConnectionPatch()
        self.fileDaoConnectionMock = self.fileDaoConnectionPatch.start()
        self.fileDaoConnectionMock.db.read.return_value = jsonString

    def _stopPatchesForExtendedLoadAllTests(self):
        self.fileDaoLoadAllPatch.stop()
        self.fileDaoConnectionPatch.stop()
        del self.fileDaoLoadAllPatch, self.fileDaoConnectionPatch
        del self.fileDaoLoadAllMock, self.fileDaoConnectionMock
