# network.proxy.py
from typing import List, ClassVar, Optional

import debug.logger as clog
from story.baseConverter import BaseConverter

logger = clog.getLogger(__name__)


class Proxy:

    def __init__(self, scheme: str = "http"):
        self.scheme = scheme
        self.endpoint = ""
        self.port = 0
        self.username = ""
        self.__pw = ""

    def __eq__(self, other) -> bool:
        return self.buildForRequest() == other.buildForRequest()

    def __repr__(self):
        info = f"<{self.__class__.__name__} scheme: {self.scheme}, endpoint: {self.endpoint}, " \
               f"port: {self.port}, username: {self.username}" \
               ">"
        return info

    @property
    def pw(self) -> str:
        # --> Add security code here when needed. <--
        return self.__pw

    def buildForRequest(self) -> str:
        if not self.isValid():
            raise ValueError("Cannot build proxy for request. Proxy has one ore more invalid "
                             "or missing values: %s",
                             f"{self.scheme}, {self.username}, <PW is private>, "
                             f"{self.endpoint}, {self.port}")

        if self.username and self.__pw:
            p = f"{self.scheme}://{self.username}:{self.__pw}@{self.endpoint}:{self.port}/"
        else:
            p = f"{self.scheme}://{self.endpoint}:{self.port}/"

        return p

    def isValid(self) -> bool:
        # Check for empty:
        if self.scheme != "http" and self.scheme != "https":
            return False
        if self.endpoint == "":
            return False
        if self.username != "" and self.pw == "":
            return False
        if self.pw != "" and self.username == "":
            return False
        # Check for prohibited chars:
        for field in [self.scheme, self.endpoint, self.username, self.pw]:
            if "#" in field:
                return False
            if ":" in field:
                return False
            if " " in field:
                return False

        return True

    @classmethod
    def make(cls, endpoint: str, port: int, username: str = "", pw: str = "", scheme: str = "http"):
        proxy = Proxy()
        proxy.scheme = scheme
        proxy.endpoint = endpoint
        proxy.port = port
        proxy.username = username
        proxy.__pw = pw
        return proxy


class StringProxyConverter(BaseConverter):
    __CURRENT_VERSION: ClassVar[float] = 1.00

    def __init__(self, source, target):
        super().__init__(source, target, allowedTypes=(Proxy, str))

    def getConverted(self):
        if self._target is Proxy:
            return self.__stringToProxy()
        return self.__proxyToString()

    def __stringToProxy(self) -> Optional[Proxy]:
        proxyStr: str = self._source

        if not self.isValidProxyString(proxyStr):
            # All error logging should have been done in the callee. No additional logging here!
            return None

        # All verification logic should have been done before!
        # We do not try/except against KeyErrors and stuff here.

        parts = proxyStr.split(":")
        hasAuthentication = len(parts) == 4
        if hasAuthentication:
            # A proxy with user and password auth. Expecting the following parts:
            # 0: IP or endpoint URL
            # 1: Port
            # 2: username
            # 3: password
            proxy = Proxy.make(endpoint=parts[0],
                               port=int(parts[1]),
                               username=parts[2],
                               pw=parts[3])

        else:
            # A proxy without auth. Expecting the following parts:
            # 0: IP or endpoint URL
            # 1: Port
            proxy = Proxy.make(endpoint=parts[0], port=int(parts[1]))

        return proxy

    def __proxyToString(self) -> Optional[str]:
        if not self._source: return None
        proxy: Proxy = self._source

        parts = list()
        parts.append(proxy.endpoint)
        parts.append(str(proxy.port))
        parts.append(proxy.username)
        parts.append(proxy.pw)

        hasAuthentication = proxy.username != "" or proxy.pw != ""
        if hasAuthentication:
            proxyStr = ":".join(parts)
        else:
            proxyStr = ":".join(parts[0:2])

        # Check if result is valid
        if StringProxyConverter.isValidProxyString(proxyStr):
            # All error logging should have been done in the callee. No additional logging here!
            return proxyStr
        else:
            return None

    @staticmethod
    def isValidProxyString(proxyStr: str) -> bool:
        """ Checks if a proxy string (raw data as loaded from file) seems valid.

        :param proxyStr: A proxy as a string
        :return: True if we think the proxy string has a valid format, else False
        """
        if proxyStr is None: return False
        # Inspect if it is a proxy which is marked deactivated by '#'

        if proxyStr.startswith("#"):
            logger.debug("Ignoring possible proxy in comment line: %s", proxyStr)
            return False

        # Inspect string as a whole
        valid = not proxyStr.startswith(":")  # must not start with colon
        valid = valid and len(proxyStr) > 0  # must not be empty
        valid = valid and proxyStr.count("\n") == 0  # no newline allowed
        valid = valid and proxyStr.count(" ") == 0  # no whitespace allowed
        valid = valid and (proxyStr.count(":") == 1 or proxyStr.count(":") == 3)  # 1 or 3 colons
        if not valid:
            logger.error("Invalid proxy string: %s", proxyStr)
            return False

        # Inspect single parts of the string
        parts = proxyStr.split(":")
        hasAuthentication = len(parts) == 4

        valid = valid and (len(parts) == 2 or len(parts) == 4)
        if not valid:
            logger.error("Invalid string proxy parts length: %s", parts)
            return False

        try:
            valid = valid and parts[1].isnumeric()  # second part is the port as int
        except KeyError:
            logger.error("Invalid proxy index length while checking port: $d (parts: %s)",
                         len(parts), parts)
            return False

        if hasAuthentication:
            try:
                # username & password must not be empty
                valid = valid and parts[2] != "" and parts[3] != ""
            except KeyError:
                logger.error("Invalid proxy index length while checking username and password: $d "
                             "(parts: %s)", len(parts), parts)
                return False

        if not valid:
            logger.error("Proxy string check summary: Invalid proxy string: %s", proxyStr)
            return False

        return True


class StringlistProxiesConverter(BaseConverter):

    def __init__(self, source, target):
        super().__init__(source, target, allowedTypes=(List[Proxy], List[str]))

    def getConverted(self):
        if self._target is List[Proxy]:
            return self.__stringlistToProxies()
        return self.__proxiesToStringlist()

    def __stringlistToProxies(self) -> List[Proxy]:
        proxyStrings = self._source
        proxies: List[Proxy] = list()
        if proxyStrings is None: return proxies

        for proxyStr in proxyStrings:
            proxy = StringProxyConverter(source=proxyStr, target=Proxy).getConverted()
            if proxy:
                proxies.append(proxy)

        return proxies

    def __proxiesToStringlist(self) -> List[str]:
        proxies: List[Proxy] = self._source
        proxyStrings = list()
        if proxies is None: return proxyStrings

        for proxy in proxies:
            proxyString = StringProxyConverter(source=proxy, target=str).getConverted()
            if proxyString:
                proxyStrings.append(proxyString)

        return proxyStrings
