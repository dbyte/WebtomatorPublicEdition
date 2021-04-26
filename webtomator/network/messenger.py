# network.messenger.py
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from typing import overload

import tinydb as tdb

from config.base import APP_USERDATA_DIR
from storage.tinyDao import TinyDao

if TYPE_CHECKING:
    from typing import ClassVar, List
    from typing import overload
    from storage.base import Dao
    from network.connection import Request
    from shop.product import Product
    from shop.shop import Shop


# TODO unit test
class Discord:
    def __init__(self, request: Request, repo: Repo = None):
        self._request = request
        self._repo = repo or Repo()  # Fallback to default repo if not given
        self._payload = defaultdict(dict)

    @overload
    async def send(self, productMsg: Product, shop: Shop):
        ...

    @overload
    async def send(self, logMsg: str):
        ...

    @overload
    async def send(self, errorMsg: str):
        ...

    async def send(self, **kwargs):
        productMsg = kwargs.get("productMsg")
        logMsg = kwargs.get("logMsg")
        errorMsg = kwargs.get("errorMsg")
        shop = kwargs.get("shop")
        """ Argument is mandatory when productMsg is given """

        apiEndpoint = self._repo.findWebhookApiEndpoint().rstrip("/")

        if productMsg:
            msgConfig = self._repo.findProductMessageConfig()
            self._setProductPayload(msgConfig, product=productMsg, shop=shop)

        elif logMsg:
            msgConfig = self._repo.findLogMessageConfig()
            self._setLogPayload(msgConfig, msgText=logMsg)

        elif errorMsg:
            msgConfig = self._repo.findErrorMessageConfig()
            self._setErrorPayload(msgConfig, msgText=errorMsg)

        else:
            raise AttributeError("None of the expected arguments were given. "
                                 f"Arguments are: {kwargs}")

        endpoint = "/".join((apiEndpoint, msgConfig.user, msgConfig.token))

        # Prepare request
        self._request.configure(
            timeout=msgConfig.timeout,
            maxRetries=msgConfig.maxRetries,
            useRandomProxy=msgConfig.useRandomProxy)
        
        postParams = self._request.Params(
            url=endpoint,
            data=self._payload,
            headers={"Content-Type": "application/json"})

        # Send message
        await self._request.post(params=postParams)

    def _setProductPayload(self, msgConfig: MessageConfig, product: Product, shop: Shop):
        if not product:
            raise AttributeError(f"No 'product' given. Actual value: {product}")
        if not shop:
            raise AttributeError(f"No 'shop' given. Actual value: {shop}")

        fields = []
        if product.basePrice:
            fields.append({"name": "Price", "value": product.getPriceWithCurrency()})

        if product.sizes:
            sizeBlock = [f"{size.sizeEU}" for size in product.sizes if size.isInStock]
            if sizeBlock:
                fields.append({"name": "Sizes", "value": "\n".join(sizeBlock)})

        self.setPayload(username=msgConfig.username,
                        title=product.name,
                        description=shop.name,
                        link=product.url,
                        thumbnailURL=product.urlThumb,
                        footer="️Webtomator © 2020 dbyte solutions",
                        fields=fields)

    def _setLogPayload(self, msgConfig: MessageConfig, msgText: str):
        self.setPayload(username=msgConfig.username, content=f"🔹{msgText}")

    def _setErrorPayload(self, msgConfig: MessageConfig, msgText: str):
        self.setPayload(username=msgConfig.username, content=f"❗️{msgText}")

    def setPayload(self, **kwargs):
        username: str = kwargs.get("username")
        content: str = kwargs.get("content")
        title: str = kwargs.get("title")
        description: str = kwargs.get("description")
        link: str = kwargs.get("link")
        thumbnailURL: str = kwargs.get("thumbnailURL")
        fields: dict = kwargs.get("fields")
        footer: str = kwargs.get("footer")

        data = dict()
        # For common data structure, see
        # https://discordapp.com/developers/docs/resources/webhook#execute-webhook

        data["username"] = username or ""
        data["content"] = content or ""

        embed = dict()
        # For 'embed' data structure, see
        # https://discordapp.com/developers/docs/resources/channel#embed-object

        if kwargs.get("title"):
            embed.update({"title": title})
        if description:
            embed.update({"description": description})
        if link:
            embed.update({"url": link})
        if thumbnailURL:
            embed.update({"thumbnail": {"url": thumbnailURL}})
        if fields:
            embed.update({"fields": fields})
        if footer:
            embed.update({"footer": {"text": footer}})

        # We may leave this out when there are no embeds
        if embed:
            data["embeds"] = list()
            data["embeds"].append(embed)

        self._payload = data


# TODO unit test
class DiscordTinyDao(TinyDao):
    _DEFAULT_PATH: ClassVar = APP_USERDATA_DIR / "Messengers.json"
    _TABLE_NAME: ClassVar = "Discord"

    def __init__(self, path: Path = None):
        path = path or self._DEFAULT_PATH
        super().__init__(path=path, table=self._TABLE_NAME)

    @overload
    def find(self, apiEndpointByType: str) -> str:
        ...

    @overload
    def find(self, messageConfig: str) -> List[MessageConfig]:
        ...

    def find(self, **kwargs):
        apiEndpointByType: str = kwargs.get("apiEndpointByType")
        messageConfig: str = kwargs.get("messageConfig")

        if messageConfig:
            return self._findMessageConfig(configName=messageConfig)

        elif apiEndpointByType:
            return self._findApiEndpointByType(apiType=apiEndpointByType)

        else:
            raise AttributeError(f"None of the expected kwargs were given. kwargs are: {kwargs}")

    def _findMessageConfig(self, configName: str) -> MessageConfig:
        query = tdb.Query().configName == configName  # prepare statement
        results = super().find(condition=query)  # raises

        try:
            decodedMessageConfig = MessageConfig(**results[0])
            return decodedMessageConfig

        except Exception as e:
            raise LookupError(f"No message configuration found. "
                              f"Search value: '{configName}'. {e}")

    def _findApiEndpointByType(self, apiType: str) -> str:
        query = tdb.Query().apiType == apiType  # prepare statement
        results = super().find(condition=query)  # raises

        try:
            endpoint = results[0].get("apiEndpoint")
            return endpoint

        except Exception as e:
            raise LookupError(f"No configured API for type '{apiType}' found. {e}")


# TODO unit test
class Repo:

    def __init__(self, dao: Dao = DiscordTinyDao()):
        self._dao = dao

    def findWebhookApiEndpoint(self) -> str:
        with self._dao as dao:
            endpoint = dao.find(apiEndpointByType="webhook")
        return endpoint

    def findProductMessageConfig(self) -> MessageConfig:
        with self._dao as dao:
            msgConfig = dao.find(messageConfig="product-msg-config")
        return msgConfig

    def findErrorMessageConfig(self) -> MessageConfig:
        with self._dao as dao:
            msgConfig = dao.find(messageConfig="error-msg-config")
        return msgConfig

    def findLogMessageConfig(self) -> MessageConfig:
        with self._dao as dao:
            msgConfig = dao.find(messageConfig="log-msg-config")
        return msgConfig


# TODO unit test
@dataclass
class MessageConfig:
    """
    Note: Attribute names must exactly correspond with keys in JSON document.
    """
    configName: str
    user: str
    token: str
    timeout: int
    maxRetries: int
    useRandomProxy: bool
    username: str
