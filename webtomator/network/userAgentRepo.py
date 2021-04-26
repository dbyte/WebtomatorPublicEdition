# network.userAgentRepo.py
import random
from typing import Optional, List

import debug.logger as clog
from network.userAgentDao import FileUserAgentDao
from storage.base import Dao

logger = clog.getLogger(__name__)


class UserAgentRepo:

    def __init__(self, dao: Dao = FileUserAgentDao()):
        self._dao = dao

    def getAll(self) -> Optional[List[str]]:
        with self._dao as dao:
            userAgents: List[str] = dao.loadAll()  # raises
        return userAgents

    def getRandomUserAgent(self) -> Optional[str]:
        userAgents = self.getAll()

        if userAgents:
            random.seed = 402918
            userAgent = random.choice(userAgents)
            logger.debug("Picked random user agent: %s", userAgent)
            return userAgent

        else:
            logger.info("Random user agent: There are no active user agents in the "
                        "repository. Returning None.")
            return None
