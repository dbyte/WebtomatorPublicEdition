# storage.fileDao.py
import json
import pathlib as pl
from abc import ABC
from typing import Optional, IO, Union, List

import debug.logger as clog
from storage.base import Dao, Connectible, Connection, PathCheckMode

logger = clog.getLogger(__name__)


class FileConnection(Connection):

    def __init__(self, path: pl.Path):
        self.__db: Optional[IO] = None
        self.__path: pl.Path = path

    @property
    def db(self) -> Optional[IO]:
        return self.__db

    @property
    def path(self) -> pl.Path:
        return self.__path

    @path.setter
    def path(self, val: pl.Path) -> None:
        self.__path = val

    def open(self):
        """ Open an existing file in a+ mode and sets __db to its handle.
        This method runs both on loading and saving data, so we have to use "a+" mode,
        since we must not erase any content if we open an existing file.
        So the connection state is hereby guaranteed to always support read/write.

        Remember to set the file pointer (seek offset) to 0 at call side, because the file
        pointer is at the end of the file if the file exists.

        Any path checks must have been done before if needed. This place is to broad for that -
        saving a file takes a different kind of path check than loading etc.

        :return: None
        """
        try:
            # 'open' runs both on loading and saving data, so we have to use "a+" mode
            # since we must not erase any content if we open an existing file.
            # So the connection state is hereby guaranteed to always support read/write.
            # Remember to set the file pointer (seek offset) to 0 at call side because the file
            # pointer is at the end of the file if the file exists.
            self.__db = open(str(self.path), "a+", encoding="utf-8")
            logger.debug("File connection succeeded at path %s", self.path)

        except Exception as e:
            self.close()
            raise e

    def close(self):
        # Explicitly ask for db is not None since db may also have a dict or list of len 0,
        # which is not what we wanna know here.
        if self.db is not None:
            self.db.close()
            self.__db = None  # IMPORTANT to invalidate; triggers __del__ if it's the last ref!
            logger.debug("File connection closed at path %s", self.path)


class FileDao(Dao, Connectible, ABC):
    """ Interface for file based data access with some basic implementation. As it does
    not completely satisfy the 'Dao' Interface, its overall behaviour has to be completed
    in inherited classes or another more concrete Interface. Therefore it should not be
    able to be initialized itself.
    """

    def __init__(self, path: pl.Path = pl.Path()):
        self.__connection = FileConnection(path)

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
            logger.debug("Connection closed on destruction of %s", self)

    @property
    def connection(self) -> FileConnection:
        return self.__connection

    def loadAll(self) -> None:
        """ Opens a file connection. Main work must be done in a child class.
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :return: None
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises
        # Important here to verify against a FILE, since that way it won't be created
        # if it not exists when we would open() it with mode "a+" !
        self.connection.verifyPath(PathCheckMode.File)  # raises

        self.connection.db.seek(0)

    def saveAll(self, data=None) -> None:
        """ Overwrite/create a file with all given data.
        Always switches back file mode to "r" (readonly) after operations.
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :param data: Data to be saved
        :return: None
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises
        # Here we check for the presence of the file's parent directory.
        # because we don't know yet if the file exists.
        self.connection.verifyPath(PathCheckMode.Directory)  # raises

        # Erase all content before writing
        self.connection.db.seek(0)
        self.connection.db.truncate(0)
        # Write data to file
        self.connection.db.write(data)  # raises
        self.connection.db.flush()  # write buffer to disk
        # After flush, once more set pointer to 0 for being ready to read all content.
        self.connection.db.seek(0)

        logger.debug("Write file success: %s", self.connection.path)

    def deleteAll(self) -> None:
        """ Deletes all CONTENT of a file - not the file itself.
        Always switches back file mode to "r" (readonly) after operations.

        We are in a DAO, so we keep the environment but delete all its data. Note that we
        do not care about any tables here, we just delete all content!

        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :return: None
        :raises:
        """
        self.connection.raiseWhenDisconnected()  # raises
        self.connection.verifyPath(PathCheckMode.File)  # raises

        try:
            # Erase all content
            self.connection.db.seek(0)
            self.connection.db.truncate(0)
            self.connection.db.flush()  # write buffer to disk
            logger.debug("Successfully deleted all content of file %s.",
                         self.connection.path.resolve())

        except Exception as e:
            raise IOError(
                f"Could not delete content of file {self.connection.path}") from e


class TextFileDao(FileDao, ABC):
    """ DAO Interface for text files with some basic behaviour. Intended to be implemented by a
    concrete DAO class as it does not completely satisfy the 'Dao' Interface.
    There is no support for table based operations here. So a file is
    supposed to be a single entity.
    """

    def __init__(self, path: pl.Path = pl.Path()):
        super().__init__(path)

        self._recordArrayKey = "data"
        self._records = None

    def loadAll(self) -> Optional[dict]:
        """ Loads all data from a text file. Raises on error!
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        In rare cases there might be a need to do a more granular separation within every read
        line. With a given recordSep different than "\n" it's possible to do that.

        :return: A dict if the parsing resulted in valid data, else None.
        :raises:
        """
        super().loadAll()  # raises

        # Read lines first as this is a pure text file.
        lines = self.connection.db.readlines()

        if not lines:
            return None

        self._records = {self._recordArrayKey: []}

        for line in lines:
            # Now call the child's hook implementations. Order of calls does matter here!
            processedStr = self._cleanupRecord(line)
            if not processedStr: continue
            processedStr = self._filterRecord(processedStr)
            if not processedStr: continue
            isValid = self._verifyRecord(processedStr)
            if not isValid: continue

            # ---------------------------------------------------------------
            # Line parsing finished, append string to list within dict.
            self._records[self._recordArrayKey].append(processedStr)
            # ---------------------------------------------------------------

        # Remove duplicates (hook with base implementation)
        self._stripDuplicates(records=self._records)  # raises

        logger.debug("%d records loaded from file.", len(self._records[self._recordArrayKey]))

        # Grab the hook to do any post processing work. This is done at any case, no records check.
        self._postprocess(self._records)

        if len(self._records[self._recordArrayKey]) == 0:
            self._records = None

        return self._records

    def saveAll(self, data: str = None) -> None:
        """ Overwrite a file with all given data.
        :param data: Newline separated string
        :return: None
        :raises: When no data to write.
        """
        if not isinstance(data, str):
            raise TypeError("Data must be of type str.")

        sourceList = data.split("\n")

        # Call the child's (or my own, if not overridden) hook implementations.
        # Order of calls does matter here!

        self._records = {self._recordArrayKey: []}

        for sourceString in sourceList:
            processedStr = self._cleanupRecord(sourceString)
            if not processedStr: continue
            processedStr = self._filterRecord(processedStr)
            if not processedStr: continue
            isValid = self._verifyRecord(processedStr)
            if not isValid: continue

            # ---------------------------------------------------------------
            # Line parsing finished, append string to list within dict.
            self._records[self._recordArrayKey].append(processedStr)
            # ---------------------------------------------------------------

        if not self._records[self._recordArrayKey]:
            raise ValueError("No data to insert. Maybe data verification failed. "
                             f"Source data: {data}")

        self._stripDuplicates(records=self._records)  # raises

        # Persist all remaining data.

        finalString = "\n".join(self._records[self._recordArrayKey])
        super().saveAll(finalString)  # raises

    def insert(self, data: str) -> None:
        """ Insert given string data into a text file. The file may already have data
        or be empty. Data gets inserted after the last line.
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :param data: Record as string. If more than one record, separate with '\n'
        :return: None
        :raises:
        """
        newDataList: List[str] = data.split("\n")
        if not newDataList:
            raise ValueError(f"No data to insert. Source data: {data}")

        # Get existing data. Will be written back together with the new data
        existingDataDict = TextFileDao.loadAll(self)

        existingDataList: List[str] = []
        if isinstance(existingDataDict, dict):
            existingDataList = existingDataDict.get(self._recordArrayKey)

        finalDataList: List[str] = existingDataList + newDataList
        finalString = "\n".join(finalDataList)

        # Run all hooks and persist all valid data.
        TextFileDao.saveAll(self, finalString)  # raises

        logger.debug("Insert record success: %s", data)

    def _cleanupRecord(self, record: str) -> Optional[str]:
        """ Hook. Override in implementing class if needed. Execution order: 1
        """
        rec = record.replace("\n", "").replace("\r", "")  # Remove all newlines
        logger.debug("Removed newline chars in: %s", rec)
        return rec if rec else None

    def _filterRecord(self, record: str) -> Optional[str]:
        """ Hook. Override in implementing class if needed. Execution order: 2
        """
        logger.debug("Skipping _filterRecord(), not implemented by inherited class.")
        return record

    def _verifyRecord(self, record: str) -> bool:
        """ Hook. Override in implementing class if needed. Execution order: 3
        """
        logger.debug("Skipping _verifyRecord(), not implemented by inherited class.")
        return True

    def _stripDuplicates(self, records: dict) -> None:
        """ Hook with base implementation. Execution order: 4
        For performance reasons, this is a one time op for all evaluated records.
        """
        if not records: return None
        if not isinstance(records, dict):
            raise TypeError(
                f"Argument 'records' must be of type dict. Data: {records}")

        recList = records.get(self._recordArrayKey)
        if recList is None:
            raise KeyError("Given records dict must have key '{self._recordArrayKey}'.")

        logger.debug("Running base duplicate strip.")

        # Remove duplicates. Note that order of elements might change by set() operation!
        countBefore = len(recList)
        recList = list(set(recList))
        countAfter = len(recList)
        countRemoved = countBefore - countAfter

        if countRemoved > 0:
            # Check if there are data left at all to insert.
            if not recList:
                records[self._recordArrayKey] = list()
                raise ValueError("No data to insert after stripping duplicates. "
                                 f"Source data: {records}")

            # Copy remaining list back dict reference(!)
            records[self._recordArrayKey] = recList

            logger.debug("Base duplicate check removed %d records", countRemoved)

    def _postprocess(self, records: dict) -> None:
        """ Hook. Override in implementing class if needed. Execution order: 5
        This is a postprocess hook to be implemented by the inherited class if needed. Called
        after all filters,  cleaners, verifiers etc. run. Take for instance the
        self.records field and do whatever is needed.

        :return: None
        """
        logger.debug("Skipping postprocessRecords(), not implemented by inherited class.")


class JsonFileDao(FileDao, ABC):
    """  Interface for JSON file based data access with some basic implementation. As it does
    not completely satisfy the 'Dao' Interface, its overall behaviour has to be completed
    in inherited classes or another more concrete Interface.
    """

    def __init__(self, path: pl.Path = pl.Path(), table: str = None):
        super().__init__(path)
        self._table = table

    def loadAll(self) -> Optional[Union[dict, list]]:
        """ Load all JSON data from a .json file. To load just a node of the root level,
        provide the appropriate key as arguments of the DAO's init.
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :return: JSON like list or a dict - depends on data structure of the JSON.
        :raises:
        """
        super().loadAll()  # raises

        try:
            jsonString = self.connection.db.read()

            # Parse JSON file. This implicitly results in a dict.
            allData = json.loads(jsonString)

        except json.JSONDecodeError as e:
            # File detected but empty or invalid format.
            raise ValueError(
                f"Unable to decode file content to JSON. "
                f"File: {self.connection.path}") from e

        except Exception as e:
            # Any other exception.
            raise Exception(
                f"An Error occurred while reading a JSON file. "
                f"File: {self.connection.path}") from e

        # Extract node which corresponds to table if given. May result in either a
        # list or a dict - depends on data structure of the JSON.
        tableData = None
        documentCount = len(allData) if isinstance(allData, (dict, list)) else 0
        if self._table:
            tableData = allData[self._table]  # must raise KeyError if not found
            documentCount = len(tableData) if isinstance(tableData, (dict, list)) else 0

        logger.debug("%d records loaded from JSON file.", documentCount)

        return tableData if tableData else allData

    def saveAll(self, data=None) -> None:
        """ Save given collection data to a .json file. Note that we completely
        overwrite existing files!
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :param data: dict or a list of dict objects
        :return: None
        :raises:
        """
        self.__verifyValidFilename()  # raises

        if (not isinstance(data, dict)) and (not isinstance(data, list)):
            raise TypeError("Failed saving JSON data. Given data must be a dict or a list "
                            "(with embedded dict) but is of type "
                            f"{type(data)}. {self.connection.path}")

        # Extend structure with a root key if self._table is given. Note that data itself must
        # not contain this table node structure. It may only contain the data inside the table.
        if self._table:
            data = {self._table: data}

        # Check if it's a valid JSON. Allow UTF-8
        try:
            jsonDump = json.dumps(data, ensure_ascii=False)

        except Exception as e:
            raise Exception(f"JSON validation failed before writing to file: {e}") from e

        # It's a valid JSON, try to persist it
        super().saveAll(data=jsonDump)  # raises

        logger.debug("Save all JSON content success: %s", self.connection.path)

    def insert(self, data: dict) -> None:
        """ Insert given collection data into a .json file. The file may already have data
        or be empty. Data gets inserted at root node, or if provided, at self._table node.
        Note: We must open a connection before running any queries. Use the
        provided context handler in client code to provide auto-releasing of the connection.

        :param data: Data document of type dict
        :return: None
        :raises:
        """
        # Handle base checks & behaviour via super (set seek to 0 etc.)
        super().loadAll()  # raises

        if not isinstance(data, dict):
            raise TypeError(
                f"Argument 'data' must be instance of dict, but type is {type(data)}")

        # We need to load all data, not just the current table's data.
        try:
            oldData = json.load(self.connection.db)  # raises

        except json.JSONDecodeError as e:
            logger.debug("No JSON content found in file for inserting. "
                         "Recovering, writing data to clean file. Error: %s", e)
            if self._table:
                oldData = {self._table: {}}
            else:
                oldData = {}

        if self._table and isinstance(oldData[self._table], dict):
            # Data should be inserted into a root object with key named self._table.
            oldData[self._table].update(data)

        elif self._table and isinstance(oldData[self._table], list):
            # Data should be appended to a root list with key named self._table.
            oldData[self._table].append(data)

        elif not self._table and isinstance(oldData, dict):
            # Data should be inserted into root object.
            oldData.update(data)

        elif not self._table and isinstance(oldData, list):
            # Data should be appended to root list. Anyway, this would be an invalid JSON.
            oldData.append(data)

        else:
            raise TypeError("Persisted data can not be updated as there is a problem "
                            f"determining the type of the loaded data. Raw data: {oldData}")

        # Completely erase old data, overwrite with new
        self.connection.db.truncate(0)
        json.dump(obj=oldData, fp=self.connection.db)  # raises

        logger.debug("Insert record success: %s", data)

    def __verifyValidFilename(self) -> None:
        filename = self.connection.path.name

        if filename == '' or filename is None:
            raise ValueError(f"Filename needed but empty: {self.connection.path}")

        elif filename[0] == '.':
            raise ValueError(
                f"Filename must not start with '.': {self.connection.path}")

        elif "/" in filename or "\\" in filename:
            raise ValueError(
                f"Filename must not contain slashes: {self.connection.path}")

        elif ".json" != self.connection.path.suffix:
            raise ValueError(f"File suffix must be 'json': {self.connection.path}")
