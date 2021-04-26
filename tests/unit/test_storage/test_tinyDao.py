# unit.test_storage.test_tinyDao.py
import os
import pathlib as pl
from stat import S_IREAD, S_IWUSR
from unittest.mock import Mock

import tinydb as tdb

from fixtures.storage import TinyDBFixture
from storage.base import Dao
from storage.tinyDao import TinyDao, TinyConnection
from unit.testhelper import WebtomatorTestCase


class TinyConnectionTest(WebtomatorTestCase):

    def setUp(self) -> None:
        # Create a TinyDB fixture
        self.dbFixture = TinyDBFixture()
        self.dbFixture.createTinyTestDB()

    def tearDown(self) -> None:
        self.dbFixture.deleteTinyTestDB()
        del self.dbFixture

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = TinyConnection

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'db')
        self.assertHasAttribute(sut, 'path')
        self.assertHasAttribute(sut, 'open')
        self.assertHasAttribute(sut, 'close')

    def test_open_shouldSetDbProperty(self):
        # Given
        path = self.dbFixture.TINYDB_TEST_PATH
        sut = TinyConnection(path)

        # When
        sut.open()

        # Then
        self.assertEqual(sut.db.storage.read(), self.dbFixture.conn.storage.read())
        sut.close()

    def test_open_shouldRaiseWhenFileNotFound(self):
        # Given
        path = pl.Path("Not/a/real/path/test_open_shouldRaiseWhenFileNotFound.json")
        sut = TinyConnection(path)

        # Then
        with self.assertRaises(FileNotFoundError):
            sut.open()
            sut.close()

    def test_close(self):
        # Given
        path = self.dbFixture.TINYDB_TEST_PATH
        sut = TinyConnection(path)

        sut.open()
        tinyReferenceBeforeClosing = sut.db
        self.assertIsNotNone(tinyReferenceBeforeClosing)  # precondition for the test

        # When
        sut.close()

        # Then
        # Expect that reference which pointed to the TinyDB has been set to None
        self.assertIsNone(sut.db)
        # Expect TinyDB itself has marked the connection as closed, which means that
        # its close() method has been called.
        self.assertFalse(tinyReferenceBeforeClosing._opened)


class TinyDaoTest(WebtomatorTestCase):

    def setUp(self) -> None:
        # Create a TinyDB fixture
        self.dbFixture = TinyDBFixture()
        self.dbFixture.createTinyTestDB()

    def tearDown(self) -> None:
        self.dbFixture.deleteTinyTestDB()
        del self.dbFixture

    def test_raiseConnectionErrorIfDisconnected(self):
        # Given
        sut: Dao = TinyDao(self.dbFixture.TINYDB_TEST_PATH)
        expectedError = ConnectionError

        # When loadAll
        with self.assertRaises(expectedError):
            sut.loadAll()

        # When saveAll
        with self.assertRaises(expectedError):
            sut.saveAll(data=None)

        # When deleteAll
        with self.assertRaises(expectedError):
            sut.deleteAll()

    def test_contextManagerShouldWorkWithSubclasses(self):
        # Given
        class ConcreteTinyDao(TinyDao):

            TABLE_NAME = self.dbFixture.TINYDB_TEST_TABLE_NAME

            def __init__(self, path=self.dbFixture.TINYDB_TEST_PATH):
                super().__init__(path=path, table=self.TABLE_NAME)

        # When
        with ConcreteTinyDao() as tinyDao:
            records = tinyDao.loadAll()

        # Then
        self.assertIsInstance(records, list)
        self.assertEqual(3, len(records))
        self.assertListEqual(self.dbFixture.TINYDB_TEST_TABLE_DATA, records)

    def test_loadAll(self):
        # Given
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH, self.dbFixture.TINYDB_TEST_TABLE_NAME) as sut:
            # When
            records = sut.loadAll()

        # Then
        self.assertIsInstance(records, list)
        self.assertEqual(3, len(records))
        self.assertListEqual(self.dbFixture.TINYDB_TEST_TABLE_DATA, records)

    def test_loadAll_shouldReturnEmptyListOnInvalidTableName(self):
        # Given
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH, "An invalid table name") as sut:
            # When
            records = sut.loadAll()

        # Then
        self.assertIsInstance(records, list)
        self.assertEqual(0, len(records))

    def test_loadAll_shouldReturnRecordsOfDefaultTableWhenNoTableNameGiven(self):
        # Given
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH) as sut:
            # When
            records = sut.loadAll()

        # Then
        self.assertIsInstance(records, list)
        self.assertEqual(2, len(records))
        self.assertListEqual(self.dbFixture.TINYDB_TEST_DEFAULT_TABLE_DATA, records)

    def test_loadAll_shouldRaiseOnGivenPathDoesNotExist(self):
        # When / Then
        with self.assertRaises(FileNotFoundError):
            with TinyDao(pl.Path("This/is/an/invalid/file.json")) as sut:
                sut.loadAll()

    def test_loadAll_shouldRaiseIOErrorOnDeepException(self):
        # Given
        noJsonFile = self.dbFixture.TINYDB_TEST_PATH.parent / "DeleteThisFile.txt"
        noJsonFile.touch(mode=0o444)  # create file with read only permissions

        # When / Then
        with self.assertRaises((IOError, PermissionError)):
            with TinyDao(noJsonFile) as sut:
                sut.loadAll()

        # Cleanup
        assert noJsonFile.is_file()
        os.chmod(str(noJsonFile), S_IWUSR | S_IREAD)  # works on windows, too
        # noJsonFile.touch(mode=0o775, exist_ok=True)
        noJsonFile.unlink()

    def test_saveAll(self):
        # Given
        newData = [
            dict(newkey_01="newvalue_01", newkey_02=267),
            dict(newkey_03="newvalue_02", newkey_04=531.8),
        ]

        # When
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH, self.dbFixture.TINYDB_TEST_TABLE_NAME) as sut:
            sut.saveAll(data=newData)

        # Then
        savedData = self.dbFixture.getAllTestTableRecords()
        self.assertIsInstance(savedData, list)
        self.assertEqual(2, len(savedData))
        self.assertListEqual(newData, savedData)

    def test_saveAll_shouldRaiseIOErrorOnInvalidData(self):
        # Given
        invalidData = ["This is a valid list type, but has 'unmapped' data."]

        # When / Then
        with self.assertRaises(IOError):
            with TinyDao(self.dbFixture.TINYDB_TEST_PATH,
                         self.dbFixture.TINYDB_TEST_TABLE_NAME) as sut:

                # noinspection PyTypeChecker
                sut.saveAll(data=invalidData)

    def test_saveAll_shouldRaiseOnGivenPathDoesNotExist(self):
        # Given
        newData = [{"one": 1}, {"two": 2}]

        # When / Then
        with self.assertRaises(FileNotFoundError):
            with TinyDao(pl.Path("This/is/an/invalid/file.json"),
                         self.dbFixture.TINYDB_TEST_TABLE_NAME) as sut:
                sut.saveAll(data=newData)

    def test_saveAll_shouldWriteRecordsToDefaultTableWhenNoTableNameGiven(self):
        # Given
        newData = [
            dict(newkey_01="newvalue_01 in default table"),
            dict(newkey_02="newvalue_02 in default table"),
        ]

        # When
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH) as sut:
            sut.saveAll(data=newData)

        # Then
        recordsInDefaultTable = self.dbFixture.conn.all()
        self.assertIsInstance(recordsInDefaultTable, list)
        self.assertEqual(2, len(recordsInDefaultTable))
        self.assertListEqual(newData, recordsInDefaultTable)

    def test_deleteAll(self):
        # Given
        countBeforeDelete = len(self.dbFixture.getAllTestTableRecords())
        assert countBeforeDelete > 0

        # When
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH, self.dbFixture.TINYDB_TEST_TABLE_NAME) as sut:
            sut.deleteAll()

        # Then
        savedData = self.dbFixture.getAllTestTableRecords()
        self.assertIsInstance(savedData, list)
        self.assertEqual(0, len(savedData))

    def test_deleteAll_shouldDeleteRecordsOfDefaultTableWhenNoTableNameGiven(self):
        # Given
        defaultTableRecordsBefore = self.dbFixture.conn.all()
        testTableRecordsBefore = self.dbFixture.getAllTestTableRecords()
        assert len(defaultTableRecordsBefore) > 0

        # When
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH) as sut:
            sut.deleteAll()

        # Then
        testTableRecordsAfter = self.dbFixture.getAllTestTableRecords()
        defaultTableRecordsAfter = self.dbFixture.conn.all()

        # These records should remain untouched:
        self.assertEqual(len(testTableRecordsBefore), len(testTableRecordsAfter))
        # Default recs should have been deleted:
        self.assertIsInstance(defaultTableRecordsAfter, list)
        self.assertEqual(0, len(defaultTableRecordsAfter))

    def test_insert(self):
        # Given
        expectedDict = dict(key_01="value01", key_02=2)

        # When
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH) as sut:
            tinyDocumentID = sut.insert(data=expectedDict)

            # Then
            # Expect that returned Tiny document ID equals 3
            self.assertEqual(3, tinyDocumentID)

            table = sut._getTableObject()
            # Expect 3 records in table (2 have been defined by the fixture)
            self.assertEqual(3, table.count(cond=lambda x: True))
            # Expect that given data is equal to inserted data
            self.assertDictEqual(expectedDict, table.get(doc_id=3))

    def test_insert_shouldRaiseIfGivenDataHasWrongType(self):
        # Given
        invalidData = Mock(name="invalid type")

        # When / Then
        with TinyDao(self.dbFixture.TINYDB_TEST_PATH) as sut:
            with self.assertRaises(TypeError):
                sut.insert(data=invalidData)

    def test_update(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        table: tdb.database.Table
        tableName = self.dbFixture.TINYDB_TEST_TABLE_NAME
        # Fixture data:
        searchKey = "uid"
        # Update with:
        expectedDocument = {
            'uid': 'bcc013d4-d7f0-4255-9aa4-4790b08e2c13',
            'key_01': 'record_02_value_for_key_01',
            'key_02': '***** A pretty new record_02_value_for_key_02 *****',
        }

        # Since we'll test with the DAO's connection to the DB file:
        self.dbFixture.closeTinyTestDB()

        # When
        with TinyDao(path=fullPath, table=tableName) as sut:
            sut.update(data=expectedDocument)

        # Then
        self.dbFixture.connectTinyTestDB()
        table = self.dbFixture.conn.table(tableName)
        condition = tdb.Query()[searchKey] == 'bcc013d4-d7f0-4255-9aa4-4790b08e2c13'
        foundDocument = table.get(condition)

        # Expect updated document (a.k.a dict) with correct new values
        self.assertDictEqual(expectedDocument, foundDocument)

    def test_update_shouldRaiseOnInvalidDataType(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        table: tdb.database.Table
        invalidDataType = Mock(name="Invalid data type")

        # When / Then
        with TinyDao(path=fullPath) as sut:
            with self.assertRaises(TypeError):
                sut.update(data=invalidDataType)

    def test_update_shouldRaiseOnInvalidUid(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        table: tdb.database.Table
        data = {'uid': ""}

        # When / Then
        with TinyDao(path=fullPath) as sut:
            with self.assertRaises(ValueError):
                sut.update(data=data)

    def test_update_shouldRaiseOnDocumentNotFound(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        table: tdb.database.Table
        nonExistentUID = 'd00a3eb7-093b-409a-893f-43cc2cad70be'
        data = {'uid': nonExistentUID}

        # When / Then
        with TinyDao(path=fullPath) as sut:
            with self.assertRaises(LookupError):
                sut.update(data=data)

    def test_update_shouldRaiseOnUidDuplicate(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        tableName = self.dbFixture.TINYDB_TEST_UID_DUP_TABLE_NAME
        table: tdb.database.Table
        recordWithDupUID = self.dbFixture.TINYDB_TEST_TABLE_WITH_UID_DUP_DATA[0]

        # When / Then
        with TinyDao(path=fullPath, table=tableName) as sut:
            with self.assertRaises(LookupError):
                sut.update(data=recordWithDupUID)

    def test_find(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        tableName = self.dbFixture.TINYDB_TEST_TABLE_NAME
        preparedCondition = tdb.Query().key_02 == "record_02_value_for_key_02"

        # When
        with TinyDao(path=fullPath, table=tableName) as sut:
            foundDocuments = sut.find(condition=preparedCondition)

        # Then
        self.assertIsInstance(foundDocuments, list)
        # Expect that one single record was found
        self.assertEqual(1, len(foundDocuments))
        # Expect that it's the record of the matching fixture
        self.assertEqual("bcc013d4-d7f0-4255-9aa4-4790b08e2c13", foundDocuments[0].get("uid"))

    def test_find_shouldRaiseOnInvalidCondition(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        tableName = self.dbFixture.TINYDB_TEST_TABLE_NAME

        invalidCondition = ""  # is of type str, should be type QueryImpl
        # When / Then
        with TinyDao(path=fullPath, table=tableName) as sut:
            with self.assertRaises(TypeError):
                # noinspection PyTypeChecker
                sut.find(condition=invalidCondition)

        # When / Then
        noneCondition = None  # should be type QueryImpl
        with TinyDao(path=fullPath, table=tableName) as sut:
            with self.assertRaises(TypeError):
                # noinspection PyTypeChecker
                sut.find(condition=noneCondition)

    def test_find_shouldReturnEmptyListIfNotFound(self):
        # Given
        fullPath = self.dbFixture.TINYDB_TEST_PATH
        tableName = self.dbFixture.TINYDB_TEST_TABLE_NAME
        notFindableCondition = tdb.Query().keyNotExists == "Neither value"

        # When
        with TinyDao(path=fullPath, table=tableName) as sut:
            foundDocuments = sut.find(condition=notFindableCondition)

        # Then
        self.assertIsInstance(foundDocuments, list)
        # Expect that list is empty
        self.assertEqual(0, len(foundDocuments))
