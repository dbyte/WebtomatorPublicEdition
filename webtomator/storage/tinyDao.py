# storage.tinyDao.py
import pathlib as pl
from abc import ABC
from typing import List, Optional

import tinydb as tdb

import debug.logger as clog
from storage.base import Dao, Connectible, Connection, PathCheckMode

logger = clog.getLogger(__name__)


class TinyConnection(Connection):

    def __init__(self, path: pl.Path):
        self.__db: Optional[tdb.TinyDB] = None
        self.__path: pl.Path = path

    @property
    def db(self) -> Optional[tdb.TinyDB]:
        return self.__db

    @property
    def path(self) -> pl.Path:
        return self.__path

    def open(self):
        # For TinyDB, it's ok to have a unique path check at this place. We do not need to
        # check for various file access situations as Tiny itself handles it.
        self.verifyPath(PathCheckMode.File)  # raises

        try:
            # Set ref to DB.
            self.__db = tdb.TinyDB(self.path)
            logger.debug("TinyDB connection succeeded at path %s", self.path)

        except Exception as e:
            raise IOError(f"TinyDB file could not be opened at: {self.path}") from e

    def close(self):
        # Explicitly ask for db is not None since db may also have a dict or list of len 0,
        # which is not what we wanna know here.
        if self.db is not None:
            self.db.close()
            self.__db = None  # IMPORTANT to invalidate; triggers __del__ if it's the last ref!
            logger.debug("TinyDB connection closed at path %s", self.path)


class TinyDao(Dao, Connectible, ABC):
    """ Interface for TinyDB data access with some basic implementation. As it does
    not completely satisfy the 'Dao' Interface, its overall behaviour is supposed to be
    completed in inherited classes or another more concrete Interface.
    """

    def __init__(self, path: pl.Path = pl.Path(), table: str = tdb.TinyDB.DEFAULT_TABLE):
        """ Constructor
        :param path: Full path to the database which in this case is a .json file
        :param table: Name of the table in the TinyDB document. If omitted/empty, it
                      will operate on TinyDB's DEFAULT_TABLE.
        """
        self.__connection = TinyConnection(path)
        self._table = table

    def __enter__(self):
        # Context manager entry. Works even in subclasses.
        self.connection.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Context manager exit. Works even in subclasses.
        self.connection.close()

    def __del__(self):
        # Close connection when last reference to TinyDao instance was invalidated.
        if self.connection is not None and self.connection.isOpen:
            self.connection.close()

    @property
    def connection(self) -> TinyConnection:
        return self.__connection

    def loadAll(self) -> Optional[List[dict]]:
        """ Builds a list of dictionaries of all the records into the given table.

        :return: A list of dictionaries of the given table. Each list element represents
        a record. Each record consists of one ore more dictionaries representing fields.
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises

        try:
            tdbTable = self._getTableObject()
            records = tdbTable.all()
            logger.debug("Table loaded: %s", repr(tdbTable))

        except Exception as e:
            raise IOError(
                f"Failed loading all table data for table '{self._table}'.") from e

        return records

    def saveAll(self, data: List[dict]) -> None:
        """ Saves a list of dictionaries of all records into the given table. All existing
        table data will be replaced by the given data.

        :param data: A list containing dictionaries
        :return: None
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises

        if data is None:
            data = list()

        try:
            tdbTable = self._getTableObject()
            tdbTable.purge()
            tdbTable.insert_multiple(data)
            logger.debug("Table data replaced: %s", repr(tdbTable))

        except Exception as e:
            raise IOError(
                f"Failed saving all table data for table '{self._table}'. Data: {data}") from e

    def deleteAll(self) -> None:
        """ Deletes all records of the given table.

        :return: None
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises

        try:
            tdbTable = self._getTableObject()
            tdbTable.purge()
            logger.debug("All table data deleted: %s", repr(tdbTable))

        except Exception as e:
            raise IOError(f"Failed deleting all table data for table '{self._table}'.") from e

    def insert(self, data: dict) -> int:
        if not isinstance(data, dict):
            raise TypeError(f"Failed inserting data into table {self._table}. "
                            f"Given 'data' must be of type dict but is type {type(data)}")

        self.connection.raiseWhenDisconnected()  # raises

        # Insert record into Shops table. It's allowed for the record to be empty, so we won't
        # check for that. Also we return the new TinyDB document id of the Shop.
        tdbTable = self._getTableObject()  # raises
        newTinyID = tdbTable.insert(data)  # raises
        return newTinyID

    def update(self, data: dict) -> None:
        """ Updates a record which has the given UID.
        The provided update-data must include the complete record (dict) and a key
        'uid' at record root level, with a UUIDv4 string as its value.

        :param data: The complete document (dict) containing a UID for a key named "uid".
        :return: None
        :raises:
        """
        if not isinstance(data, dict):
            raise TypeError(f"Failed updating data in table {self._table}. "
                            f"Given 'data' must be of type dict but is type {type(data)}")

        uid = data.get("uid", None)

        if uid is None:
            raise TypeError(f"Failed updating data in table {self._table}. "
                            f"A 'uid' key must be contained in given data but was not found. "
                            f"Data: {data}")

        if uid == "":
            raise ValueError(f"Failed updating data in table {self._table}. "
                             f"The 'uid' value is needed but empty. Data: {data}")

        self.connection.raiseWhenDisconnected()  # raises

        table = self._getTableObject()

        # Prepare statement
        condition = tdb.Query().uid == uid

        # Find occurrences of uid. We expect a list with one single element.
        # Returns list with 0 elements if not found.
        results: List[tdb.database.Document] = table.search(cond=condition)

        if not results:
            raise LookupError(
                f"Failed updating database. UID {uid} not found in table '{self._table}'")

        # Finding multiple results is supposed to be an error
        # since we're searching for a UUIDv4
        if len(results) > 1:
            raise LookupError(
                f"Failed updating database. UID {uid} found {len(results)} times in "
                f"table '{self._table}'. Expected only one. "
                "Check your database for UID duplicates!"
            )

        table.update(data, condition)

    def find(self, condition: tdb.queries.QueryImpl) -> List[dict]:
        """ Find all documents which match the given search condition.

        :param condition: Sort of prepared statement for TinyDB, of type 'QueryImpl'.
        :return: The list of documents that match the search condition or
                 an empty list if not found.
        """
        if condition is None:
            raise TypeError(f"Failed search in table {self._table}. "
                            f"'condition' argument with a TinyDB Query must be given but uid is "
                            f"None.")

        if not isinstance(condition, tdb.queries.QueryImpl):
            raise TypeError(f"Failed search in table {self._table}. "
                            f"'condition' value must be a 'QueryImpl' object.")

        self.connection.raiseWhenDisconnected()  # raises

        table = self._getTableObject()

        # Find occurrences of uid. We expect a list with one single element.
        # Returns list with 0 elements if not found.
        results: List[tdb.database.Document] = table.search(cond=condition)

        return results

    def _getTableObject(self) -> tdb.database.Table:
        """ Caution: Creates new table with name self._table if not exists.
        :return: TinyDB Table object
        """
        tdbTable: tdb.database.Table = self.connection.db.table(name=self._table)
        return tdbTable
