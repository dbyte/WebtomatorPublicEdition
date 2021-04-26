# network.userAgentDao.py
import pathlib as pl
from typing import ClassVar, Optional, List

import debug.logger as clog
from config.base import APP_USERDATA_DIR
from storage.fileDao import TextFileDao

logger = clog.getLogger(__name__)


class FileUserAgentDao(TextFileDao):
    """ Loads a .txt file line by line, whereas each line represents a user agent.

    Lines starting with '#' are interpreted as an inactive user agent.
    """
    __DEFAULT_PATH: ClassVar = APP_USERDATA_DIR / "UserAgents.txt"

    def __init__(self, filepath: pl.Path = None):
        """Omit filepath if default path is required. Path can also be changed
        later via self.path .

        :param filepath: Optional. Full path to proxy repo
        """
        self.__userAgentStringlist = None
        path = filepath or FileUserAgentDao.__DEFAULT_PATH
        super().__init__(path=path)

    def loadAll(self) -> Optional[List[str]]:
        """ Tries to load user agents from a text file and set a string list
        of it. If no file path was given during init, we load from the
        default path. You're also free to change the path from outside via
        `self.path` after initialization.

        :return: String list of user agents.
        :raises:
        """
        super().loadAll()  # raises
        # Note that super() method also runs/triggers hooks like _postprocess() etc. and
        # by default also strips duplicates.

        if self.__userAgentStringlist:
            return self.__userAgentStringlist

        else:
            logger.warning("No valid user agents found in repo file. Please check if they are "
                           "marked as inactive by a '#' character at line start. Make sure"
                           "your user agents file is empty if you don't need them.")
            return None

    def update(self, data: str):
        # Makes no sense to update plain text data.
        raise NotImplementedError

    def find(self, **kwargs):
        raise NotImplementedError

    def insert(self, data: str) -> None:
        """ Add a user agent to the database.

        :param data: A single user agent string
        :return: None
        :raises:
        """
        super().insert(data=data)  # raises
        # Note that super() method also runs/triggers hooks like _postprocess() etc. and
        # by default also strips duplicates.

    # Override hook implementations of superclass.
    # 1.
    def _cleanupRecord(self, record: str) -> Optional[str]:
        """ Called by superclass.
        :param record: A single user agent string
        :return: A cleaned up user agent string or None if nothing is left after cleaning
        """
        logger.debug("Before cleanup: %s", record.replace("\n", "\\n"))
        tempRec = super()._cleanupRecord(record)  # run default cleanup
        if not tempRec: return None
        tempRec = record.strip()  # Remove leading/trailing whitespace
        logger.debug("After cleanup: %s", tempRec)
        return tempRec if tempRec else None

    # 2.
    def _filterRecord(self, record: str) -> Optional[str]:
        """ Called by superclass.
        :param record: A single user agent string
        :return: The same string if no filter was applied, else None
        """
        if record.startswith("#"):
            logger.debug("Ignoring possible user agent in comment line: %s", record)
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
            self.__userAgentStringlist = flatList
