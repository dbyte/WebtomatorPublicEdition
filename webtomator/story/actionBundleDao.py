# actionBundleDao.py

import pathlib as pl
import typing as tp

import debug.logger as clog
import storage.fileDao as filedao
from config.base import APP_USERDATA_DIR
from story.actionBundle import ActionBundle
from story.actionBundleConverter import DictActionBundleConverter

logger = clog.getLogger(__name__)


class JSONActionBundleDao(filedao.JsonFileDao):
    _DEFAULT_DIR: tp.ClassVar[pl.Path] = APP_USERDATA_DIR / "actionbundles"
    _TABLE_NAME: tp.ClassVar[str] = "ActionBundles"

    def __init__(self, filepath: str = None):
        if not filepath:
            thePath = self._DEFAULT_DIR
        else:
            thePath = pl.Path(filepath)
        super().__init__(path=thePath, table=self._TABLE_NAME)

    def loadAll(self) -> ActionBundle:
        """
        :return: An instance of class ActionBundle if loading succeeds
        :raises:
        """
        dataDict = None
        try:
            expectedList = super().loadAll()
            # As a rule we expect a list with one single element, which represents an
            # ActionBundle. We would extend handling here when we wish to receive
            # multiple ActionBundles.
            if isinstance(expectedList, list):
                dataDict = expectedList[0]

        except Exception as e:
            raise Exception(
                f"Failed loading ActionBundle {self.connection.path}") from e

        else:
            converter = DictActionBundleConverter(source=dataDict, target=ActionBundle,
                                                  table=self._TABLE_NAME)
            return converter.getConverted()

    def saveAll(self, data=None) -> None:
        if not isinstance(data, ActionBundle):
            raise TypeError(
                f"Argument 'data' must be instance of ActionBundle, but type is {type(data)}")

        converter = DictActionBundleConverter(source=data, target=dict, table=self._TABLE_NAME)
        data: dict = converter.getConverted()
        if data:
            super().saveAll(data=data)  # raises

    def insert(self, data: ActionBundle) -> None:
        """ Inserts an ActionBundle record into the JSON document. Appends it to the root node
        of key _TABLE_NAME.

        :param data: ActionBundle object
        :return: None
        :raises:
        """
        if not isinstance(data, ActionBundle):
            raise TypeError(
                f"Argument 'data' must be instance of ActionBundle, but type is {type(data)}")

        converter = DictActionBundleConverter(source=data, target=dict, table=self._TABLE_NAME)
        data: dict = converter.getConverted()

        if data:
            super().insert(data=data)  # raises

    def update(self, data):
        raise NotImplementedError

    def find(self, **kwargs):
        raise NotImplementedError
