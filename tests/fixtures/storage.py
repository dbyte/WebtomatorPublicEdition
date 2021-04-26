# fixtures.storage.py
import typing as tp
from pathlib import Path

import tinydb as tdb

from storage.base import Connection

__MY_ROOT = Path(__file__).parent
STORAGE_TEST_PATH: Path = __MY_ROOT / "../resources/userdata/"
assert STORAGE_TEST_PATH.is_dir()


class TinyDBFixture:

    TINYDB_TEST_PATH: Path = STORAGE_TEST_PATH / "SomeTinyDB.json"
    TINYDB_TEST_TABLE_NAME: str = "TestTable"
    TINYDB_TEST_UID_DUP_TABLE_NAME: str = "WithUidDubs"

    TINYDB_TEST_TABLE_DATA: list = [
        {
            'uid': '0a94dd8b-ec1a-4610-9cd3-daa7a9c1afcb',
            'key_01': 'record_01_value_for_key_01',
            'key_02': 'record_01_value_for_key_02',
        },
        {
            'uid': 'bcc013d4-d7f0-4255-9aa4-4790b08e2c13',
            'key_01': 'record_02_value_for_key_01',
            'key_02': 'record_02_value_for_key_02',
        },
        {
            'uid': '662dd971-8434-456b-87da-b601622596a7',
            'fruitList': [
                'apple', 'banana', 'strawberry'
            ]
        }
    ]

    TINYDB_TEST_TABLE_WITH_UID_DUP_DATA: list = [
        {
            'uid': '849b3296-f9ea-4e21-a6e9-740e191258c7',
            'key_01': 'record_01_value_for_key_01',
            'key_02': 'record_01_value_for_key_02',
        },
        {
            'uid': '849b3296-f9ea-4e21-a6e9-740e191258c7',
            'key_01': 'record_02_value_for_key_01',
            'key_02': 'record_02_value_for_key_02',
        }
    ]

    TINYDB_TEST_DEFAULT_TABLE_DATA: list = [
        {
            'key_01': 'defaultTable_record_01_value_for_key_01',
            'key_02': 'defaultTable_record_01_value_for_key_02',
        },
        {
            'key_01': 'defaultTable_record_02_value_for_key_01',
            'key_02': 'defaultTable_record_02_value_for_key_02',
        }
    ]

    def __init__(self):
        self.conn: tp.Optional[tdb.TinyDB] = None

    def connectTinyTestDB(self):
        # Note: Creates a DB file if not exists
        # Always returns a reference to the DB.
        self.conn = tdb.TinyDB(str(self.TINYDB_TEST_PATH))

    def closeTinyTestDB(self):
        # Close DB but keep file.
        self.conn.close()

    def createTinyTestDB(self):
        self.connectTinyTestDB()

        # Add 2 documents to TinyDB's default table
        self.conn.purge()
        self.conn.insert_multiple(self.TINYDB_TEST_DEFAULT_TABLE_DATA)

        # Additionally add a TestTable with 3 documents
        table: tdb.database.Table = self.conn.table(self.TINYDB_TEST_TABLE_NAME)
        table.purge()
        table.insert_multiple(self.TINYDB_TEST_TABLE_DATA)

        # Additionally add a TestTable with 2 Documents which have a duplicated UID
        table: tdb.database.Table = self.conn.table(self.TINYDB_TEST_UID_DUP_TABLE_NAME)
        table.purge()
        table.insert_multiple(self.TINYDB_TEST_TABLE_WITH_UID_DUP_DATA)

        # Do NOT close db connection here.

    def deleteTinyTestDB(self):
        self.closeTinyTestDB()
        assert self.TINYDB_TEST_PATH.is_file()
        self.TINYDB_TEST_PATH.unlink()

    def getAllTestTableRecords(self) -> list:
        return self.conn.table(self.TINYDB_TEST_TABLE_NAME).all()


class ConnectionImplFixture(Connection):

    def __init__(self):
        self.__db = "dummy"
        self.__path: Path = Path("some/path/to/db")

    @property
    def db(self):
        return self.__db

    @db.setter
    def db(self, val):
        self.__db = val

    @property
    def path(self) -> Path:
        return self.__path

    @path.setter
    def path(self, val: Path):
        self.__path = val

    def open(self): pass

    def close(self): pass