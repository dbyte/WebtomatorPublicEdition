# network.connection.py
from __future__ import annotations

import asyncio
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

import aiohttp

import debug.logger as clog
from network.proxyRepo import ProxyRepo
from network.userAgentRepo import UserAgentRepo

if TYPE_CHECKING:
    from typing import Union, Optional, Any
    from network.proxy import Proxy

logger = clog.getLogger(__name__)


# TODO unit test
class Session(ABC):

    @abstractmethod
    def __init__(self, proxyRepo: ProxyRepo, userAgentRepo: UserAgentRepo, *args, **kwargs):
        self._proxyRepo: ProxyRepo = proxyRepo
        self._userAgentRepo: UserAgentRepo = userAgentRepo

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def get(self, *args, **kwargs):
        ...

    @abstractmethod
    async def post(self, *args, **kwargs):
        ...

    def getRandomProxy(self) -> Proxy:
        randomProxy = self._proxyRepo.getRandomProxy()
        if not randomProxy:
            raise LookupError(
                "A web proxy is required but was not found in the repository.")

        return randomProxy

    def getRandomUserAgent(self) -> str:
        randomAgent = self._userAgentRepo.getRandomUserAgent()
        if not randomAgent:
            raise LookupError(
                "A user agent is required but was not found in the repository.")

        return randomAgent


# TODO unit test
class AioHttpSession(aiohttp.ClientSession, Session):
    """ aioHttp session adapter which conforms to interface 'Session'. Try to
    set as few properties as possible here. Instead, set properties for
    each request to reach max flexibility.
    """

    def __init__(self,
                 proxyRepo: ProxyRepo = ProxyRepo(),
                 userAgentRepo: UserAgentRepo = UserAgentRepo(),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        Session.__init__(self, proxyRepo, userAgentRepo)
        logger.debug("AioHttpSession initialized")

    async def close(self) -> None:
        await asyncio.sleep(0.1)  # needed to get rid of "unclosed connection" errors
        await super().close()
        logger.debug("AioHttpSession closed")


# TODO unit test
class Request(ABC):
    """ Use this for any network request, instead of the http lib's session.get().
    Note: In general, a request object is configured only once for each class that owns it.

    Beforehand, a 'Session' object must be created. This object has to be passed in to
    the constructor of this class as a 'session' argument.
    """

    @dataclass
    class Params:
        """ Data wrapper around `fetch` and `post` methods. Get one and initialize it
         within the client right before actually executing a request.
         Inject into `fetch` or `post` method. """

        url: str
        """ A file path to the file where we persist the post data to test against them """

        data: Optional[Any] = None
        """ Data to post """

        headers: Optional[dict] = None
        """ Optional headers as a dictionary """

    def __init__(self, session: Session):
        self._session: Session = session
        """ Initialized session """

        self._maxRetries: int = 0
        """ Determines how many times we try after a bad response.
        The default value should be changed from outside with help of method `configure` """

        self._timeout: int = 0
        """ Response timeout in seconds.
        The default value should be changed from outside with help of method `configure`. """

        self._useRandomProxy: bool = True
        """ True if a random proxy should be generated before each post.
        The default value should be changed from outside with help of method `configure`. """

    def configure(self, timeout: int, maxRetries: int, useRandomProxy: bool):
        self._timeout = timeout
        self._maxRetries = maxRetries
        self._useRandomProxy = useRandomProxy

    @abstractmethod
    async def fetch(self, params: Params, callCount=0) -> 'Response':
        ...

    @abstractmethod
    async def post(self, params: Params, callCount=0) -> 'Response':
        ...


# TODO unit test
class AioHttpRequest(Request):

    def __init__(self, session: Session):
        super().__init__(session=session)

    async def fetch(self, params: Request.Params, callCount=0) -> 'Response':
        """ Get data from URL. Proxy and UserAgent are generated for each GET-request.

        :param params: See class `Request.Params`
        :param callCount: This method is recursive, pass in the iteration count
        :return: Response object
        """
        callCount += 1
        isExceededCalls, exceededCallsMsg = \
            self._isExceededMaxRetries(self._maxRetries, callCount, params.url)

        if isExceededCalls:
            return Response(data=None, text=None, error=ConnectionError(exceededCallsMsg))

        if not self._timeout:
            self._timeout = 10
            logger.warning("No timeout was given, falling back to timeout=%d. %s",
                           self._timeout, params.url)

        proxyStr = None
        if self._useRandomProxy:
            proxy = self._session.getRandomProxy()  # raises
            proxyStr = proxy.buildForRequest()

        if not params.headers:
            params.headers = {}

        agent = self._session.getRandomUserAgent()  # raises
        params.headers.update({'User-Agent': agent})

        result: Optional[aiohttp.ClientResponse] = None

        try:
            # This handler does not close the session! It just closes the connection to the server.
            async with self._session.get(url=params.url,
                                         headers=params.headers,
                                         proxy=proxyStr,
                                         timeout=self._timeout) as result:

                status = result.status

                if status == 200:
                    logger.debug("GET response status %d ::: %s", status, params.url)
                    text = await result.text()
                    return Response(data=result, text=text, error=None)

                elif status > 200:
                    delay = Tools.getRandomBetween(1, 3, step=0.3)
                    logger.debugConn("GET bad status %d. Retry in %.2f seconds: %s, Proxy: %s, "
                                     "UA: %s", status, delay, params.url, proxyStr, agent)

                    await asyncio.sleep(delay)
                    response = await self.fetch(params=params, callCount=callCount)
                    return response

        except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as e:
            logger.debugConn("%s: %s. Retry instantly: %s", Tools.getTypeString(e), e, params.url)
            # Retry with new random proxy
            await asyncio.sleep(0.25)
            response = await self.fetch(params=params, callCount=callCount)
            return response

        except asyncio.TimeoutError as e:
            delay = Tools.getRandomBetween(1, 3, step=0.3)
            logger.debugConn("%s: Retry in %.2f seconds: %s, Proxy: %s, UA: %s",
                             Tools.getTypeString(e), delay, params.url, proxyStr, agent)

            await asyncio.sleep(delay)
            response = await self.fetch(params=params, callCount=callCount)
            return response

        except Exception as e:
            logger.error("General error, won't retry: %s: %s %s",
                         Tools.getTypeString(e), e, params.url, exc_info=True)
            return Response(data=None, text=None, error=ConnectionError(f"{e}"))

        finally:
            if result:
                if not result.closed:
                    result.close()

    async def post(self, params: Request.Params, callCount=0):
        """ Post a request.

        :param params: See class `Request.Params`
        :param callCount: Counts recursive calls, must be 0 at initial call.
        :return: Response object
        """
        agent = self._session.getRandomUserAgent()  # raises
        proxyStr = None
        if self._useRandomProxy:
            proxy = self._session.getRandomProxy()  # raises
            proxyStr = proxy.buildForRequest()

        callCount += 1
        isExceededCalls, exceededCallsMsg = \
            self._isExceededMaxRetries(self._maxRetries, callCount, params.url)

        if isExceededCalls:
            return Response(data=None, text=None, error=ConnectionError(exceededCallsMsg))

        if not self._timeout:
            self._timeout = 10
            logger.warning("No timeout was given, falling back to timeout=%d. %s",
                           self._timeout, params.url)
        if not params.headers:
            raise ValueError(f"Failed request post: No headers given. {params.url}")
        if not params.data:
            raise ValueError(f"Failed request post: No data to post. {params.url}")

        params.headers.update({'User-Agent': agent})

        result: Optional[aiohttp.ClientResponse] = None

        try:
            # This handler does not close the session! It just closes the connection to the server.
            async with self._session.post(url=params.url,
                                          json=params.data,
                                          headers=params.headers,
                                          proxy=proxyStr,
                                          timeout=self._timeout) as result:
                status = result.status
                if status == 200 or 204:
                    logger.debug("POST response status %d ::: %s", status, params.url)
                    return Response(data=result, text="", error=None)

                elif status > 200:
                    delay = Tools.getRandomBetween(1, 3, step=0.3)
                    logger.debugConn("POST bad status %d. Retry in %.2f seconds: %s, Proxy: %s, "
                                     "UA: %s", status, delay, params.url, proxyStr, agent)

                    await asyncio.sleep(delay)
                    response = await self.post(params=params, callCount=callCount)

                    return response

        except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as e:
            logger.debugConn("%s: %s. Retry instantly: %s", Tools.getTypeString(e), e, params.url)
            # Retry
            await asyncio.sleep(0.25)
            response = await self.post(params=params, callCount=callCount)

            return response

        except asyncio.TimeoutError as e:
            delay = Tools.getRandomBetween(1, 3, step=0.3)
            logger.debugConn("%s: Retry in %.2f seconds: %s, Proxy: %s, UA: %s",
                             Tools.getTypeString(e), delay, params.url, proxyStr, agent)
            # Retry
            await asyncio.sleep(delay)
            response = await self.post(params=params, callCount=callCount)

            return response

        except Exception as e:
            logger.error("General error, won't retry: %s: %s %s",
                         Tools.getTypeString(e), e, params.url, exc_info=True)
            return Response(data=None, text=None, error=ConnectionError(f"{e}"))

        finally:
            if result and not result.closed:
                result.close()

    @staticmethod
    def _isExceededMaxRetries(maxRetries, callCount, url) -> (bool, str):
        if callCount - 1 <= maxRetries:
            return False, ""
        else:
            msg = f"Still failed after {callCount - 1} tries, giving up {url}"
            logger.error(msg)
            return True, msg


# TODO unit test
class Response:
    """ Data wrapper around a request's response
    """

    def __init__(self,
                 data: Optional[Union[aiohttp.ClientResponse, str]],
                 text: Optional[str],
                 error: Optional[Exception]):
        self._data = data  # Determined to be None if 'error' is not None
        self._text = text  # Textual content of the response or None
        self._error = error  # Determined to be None if 'data' and 'text' is not None

    def __repr__(self):
        textShort = self.text[0:30] if self.text else None
        errorRepr = repr(self.error) if self.error else None
        info = f"<{self.__class__.__name__} text: {textShort}..., error: {errorRepr}" \
               ">"
        return info

    @property
    def data(self) -> Optional[Union[aiohttp.ClientResponse]]:
        return self._data

    @property
    def text(self) -> Optional[str]:
        return self._text

    @property
    def error(self) -> Optional[Exception]:
        return self._error


# TODO unit test
class Tools:

    @staticmethod
    def getRandomBetween(start: int, stop: int, step: float) -> float:
        if step <= 0 or step > 1:
            raise ValueError("Step must be between 0 and 1")
        factor = int(round(1 / step))
        values = [float(x * step) for x in range(factor * start, factor * stop + 1)]
        if start not in values:
            values.insert(0, start)
        if stop not in values:
            values.append(stop)

        return max(0.00, round(random.choice(values), 2))

    @staticmethod
    def getTypeString(instance: object) -> str:
        cls = getattr(instance, "__class__", None)
        return getattr(cls, "__name__", "[No error type found]")
