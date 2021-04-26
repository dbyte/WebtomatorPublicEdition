# storage.base.py
import logging
import pathlib as pl
import typing as tp
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import overload

logger = logging.getLogger(__name__)


class PathCheckMode(Enum):
    File = 1
    Directory = 2


class Connection(ABC):

    @property
    @abstractmethod
    def db(self):
        ...

    @db.setter
    @abstractmethod
    def db(self, val):
        ...

    @property
    @abstractmethod
    def path(self) -> pl.Path:
        ...

    @path.setter
    @abstractmethod
    def path(self, val: pl.Path):
        ...

    @abstractmethod
    def open(self):
        ...

    @abstractmethod
    def close(self):
        ...

    @property
    def isOpen(self) -> bool:
        # Explicitly ask for None here!
        return self.db is not None

    def raiseWhenDisconnected(self):
        """ Convenience method for raising, when connection needed but not established.
        :return: None
        :raises:
        """
        if not self.isOpen:
            raise ConnectionError(
                "DAO operation refused: No connection. Open a connection before "
                "running any operations on the database.")

    def verifyPath(self, mode: PathCheckMode) -> None:
        """ Pre-check a given path before doing any operations on file system.

        :param mode: Allowed values are 'file' or 'directory'
        :return: None
        :raises: ValueError, FileNotFoundError, NotADirectoryError
        """
        if not self.path or self.path.name == "":
            raise ValueError("No path given.")

        if mode == PathCheckMode.File:
            if not self.path.is_file():
                raise FileNotFoundError(f"Path does not point to a file: {self.path}")

        elif mode == PathCheckMode.Directory:
            if not self.path.parent.is_dir():
                raise NotADirectoryError(f"Path does not point to a directory: {self.path}")

        else:
            raise NotImplementedError(
                f"'mode' argument must be 'file' or 'directory'. Current: '{mode}'")

        logger.debug("Path check success: %s", self.path)


class Identifiable(ABC):

    @property
    @abstractmethod
    def uid(self) -> str: ...

    @uid.setter
    @abstractmethod
    def uid(self, val: str) -> None: ...

    @classmethod
    def generateUID(cls) -> str:
        return str(uuid.uuid4())


class Connectible(ABC):

    @property
    @abstractmethod
    def connection(self) -> Connection: ...

    @connection.setter
    @abstractmethod
    def connection(self, val: Connection): ...


class Dao(ABC):

    @abstractmethod
    def loadAll(self): ...

    @overload
    @abstractmethod
    def saveAll(self): ...

    @overload
    @abstractmethod
    def saveAll(self, data: tp.Any): ...

    @abstractmethod
    def saveAll(self, **kwargs): ...

    @abstractmethod
    def deleteAll(self): ...

    @abstractmethod
    def insert(self, data: tp.Any): ...

    @abstractmethod
    def update(self, data: tp.Any): ...

    @abstractmethod
    def find(self, **kwargs): ...
