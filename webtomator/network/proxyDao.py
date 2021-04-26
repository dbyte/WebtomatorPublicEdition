# network.proxyDao.py
import pathlib as pl
from typing import ClassVar, Optional, List

import debug.logger as clog
from config.base import APP_USERDATA_DIR
from network.proxy import StringProxyConverter, StringlistProxiesConverter, Proxy
from storage.fileDao import TextFileDao

logger = clog.getLogger(__name__)


class FileProxyDao(TextFileDao):
    """ Loads a .txt file line by line, whereas each line represents a proxy in the
    following format:

    endpoint:port:user:password OR endpoint:port

    Whitespaces are stripped. Lines starting with '#' are interpreted as an inactive proxy.
    """
    __DEFAULT_PATH: ClassVar = APP_USERDATA_DIR / "Proxies.txt"

    def __init__(self, filepath: pl.Path = None):
        """Omit filepath if default path is required. Path can also be changed
        later via self.path .

        :param filepath: Optional. Full path to proxy repo
        """
        self.__proxyStringList = None
        path = filepath or FileProxyDao.__DEFAULT_PATH
        super().__init__(path=path)

    def loadAll(self) -> Optional[List[Proxy]]:
        """ Tries to load proxies from a text file and set a Proxy
        list from it. If no file path was given during init, we load from the
        default path. You're also free to change the path from outside via
        `self.path` after initialization.

        :return: List of Proxy objects.
        :raises: Exception
        """
        super().loadAll()  # raises
        # Note that super() method also runs/triggers hooks like _postprocess() etc.

        if self.__proxyStringList:
            converter = StringlistProxiesConverter(source=self.__proxyStringList,
                                                   target=List[Proxy])
            return converter.getConverted()

        else:
            logger.warning("No valid proxy data found in repo file. Please check if they are "
                           "marked as inactive by a '#' character at line start. Make sure"
                           "your proxy file is empty if you don't need proxies.")
            return None

    def update(self, data: Proxy):
        # Makes no sense to update plain text data.
        raise NotImplementedError

    def find(self, **kwargs):
        raise NotImplementedError

    def insert(self, data: Proxy) -> None:
        """ Add a Proxy to the database.

        :param data: A single Proxy object
        :return: None
        :raises:
        """
        converter = StringProxyConverter(source=data, target=str)
        proxyStr = converter.getConverted()
        super().insert(data=proxyStr)  # raises

    # Override/implement hook implementations of superclass.
    # 1.
    def _cleanupRecord(self, record: str) -> Optional[str]:
        """ Called by superclass.
        :param record: A single proxy string
        :return: A cleaned up proxy string or None if nothing is left after cleaning
        """
        logger.debug("Before cleanup: %s", record.replace("\n", "\\n"))
        tempRec = super()._cleanupRecord(record)  # run default cleanup
        if not tempRec: return None
        tempRec = record.strip()  # Remove all whitespace
        logger.debug("After cleanup: %s", tempRec)
        return tempRec if tempRec else None

    # 2.
    def _filterRecord(self, record: str) -> Optional[str]:
        """ Called by superclass.
        :param record: A single proxy string
        :return: The same string if no filter was applied, else None
        """
        if not StringProxyConverter.isValidProxyString(record):
            logger.debug("Record sorted out by filter: %s", record)
            return None
        return record

    # 3.
    def _postprocess(self, records: dict):
        """ Called by superclass after all record processing has been finished.

        :param records: The full-processed record dictionary.
        """
        # Create a flat list of the record dict
        if not isinstance(records, dict): return
        flatList = records.get(self._recordArrayKey)
        if flatList:
            self.__proxyStringList = flatList
