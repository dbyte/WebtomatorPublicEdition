# network.proxyRepo.py
import random
from typing import Optional, List

import debug.logger as clog
from network.proxy import Proxy
from network.proxyDao import FileProxyDao
from storage.base import Dao

logger = clog.getLogger(__name__)


class ProxyRepo:

    def __init__(self, dao: Dao = FileProxyDao()):
        self._dao = dao

    def getAll(self) -> Optional[List[Proxy]]:
        with self._dao as dao:
            proxies: List[Proxy] = dao.loadAll()  # raises
        return proxies

    def addProxy(self, proxy: Proxy) -> None:
        if proxy.isValid():

            with self._dao as dao:
                dao.insert(data=proxy)  # raises

            logger.debug("Added proxy to repo. Proxy: ENDPOINT: %s, PORT: %d, "
                         "USER: %s", proxy.endpoint, proxy.port, proxy.username)

        else:
            raise ValueError(
                "Proxy not added to repo because of one ore more invalid fields. "
                f"Values are: {proxy.scheme}, {proxy.username}, <PW is private>, "
                f"{proxy.endpoint}, {proxy.port}"
            )

    def getRandomProxy(self) -> Optional[Proxy]:
        proxies = self.getAll()

        if proxies:
            random.seed = 300119
            proxy = random.choice(proxies)
            logger.debug("Picked random proxy: ENDPOINT: %s, PORT: %d, USER: %s",
                         proxy.endpoint, proxy.port, proxy.username)
            return proxy

        else:
            logger.info("Random proxy: There are no active proxies in the "
                        "repository. Returning None.")
            return None
