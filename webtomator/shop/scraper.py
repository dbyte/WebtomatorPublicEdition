# shop.scraper.py
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

import debug.logger as clog
from scraper.base import Scraper
from shop.product import Size

if TYPE_CHECKING:
    from network.connection import Request
    import network.messenger as msn
    from shop.product import Product
    from shop.shop import Shop
    from shop.shopRepo import ShopRepo

logger = clog.getLogger(__name__)
ProductChanged = bool  # type alias
ShopChanged = bool  # type alias


# TODO unit tests
class ShopScraper(Scraper, ABC):
    _scrapee: Shop  # type-hint: downcast to concrete type
    _scrapeeRepo: ShopRepo  # dito

    def __init__(self,
                 scrapee: Shop,
                 scrapeeRepo,
                 request: Request,
                 messenger: msn.Discord):

        super().__init__(scrapee=scrapee,
                         scrapeeRepo=scrapeeRepo,
                         request=request,
                         messenger=messenger)

    async def run(self) -> None:
        logger.debug("ShopScraper: run() called. %s", self._scrapee.url)
        # Execute runMainItem and runAllLineItems concurrently,
        # but wait until BOTH are completed before returning.
        await asyncio.gather(self._requestShop(), self._requestAllProducts())
        uniIcon = "🔸" if self._failCount > 0 else "🔹"
        logger.info("%sShopScraper completed. Total fails: %d. %s",
                    uniIcon, self._failCount, self._scrapee.url)

    async def _requestShop(self):
        logger.debug("Request shop %s", self._scrapee.url)
        # Wait for heavy lift to be finished. Meanwhile, suspend me for other tasks.
        fetchParams = self._request.Params(url=self._scrapee.url)
        response = await self._request.fetch(params=fetchParams)

        if response.error: self._failCount += 1
        logger.debug("Finished shop request %s", self._scrapee.url)
        # Process the data we got
        if response.text:
            soup = BeautifulSoup(response.text, "html.parser")
            shopChanged = await self._setShopName(soup)
            self._scrapee.setLastScanNow()
            if shopChanged:
                # Process things that have to be done when we got updated data for the shop
                self._scrapeeRepo.update(shop=self._scrapee)

    async def _requestAllProducts(self):
        logger.debug("Start requesting all products. %s", self._scrapee.url)
        # Start product requests concurrently! This greatly decreases completion time.
        productRunners = [self._requestProduct(product=p) for p in self._scrapee.products]
        # But while waiting for all tasks to be completed, suspend me for other tasks.
        await asyncio.gather(*productRunners)
        logger.debug("All product requests completed. %s", self._scrapee.url)

    async def _requestProduct(self, product: Product):
        logger.debug("Request product %s", product.url)
        # Wait for heavy lift to be finished. Meanwhile, suspend me for other tasks.
        fetchParams = self._request.Params(url=product.url)
        response = await self._request.fetch(params=fetchParams)

        if response.error: self._failCount += 1
        # Process the data we got
        if response.text:
            soup = BeautifulSoup(response.text, "html.parser")
            results = await asyncio.gather(self._setProductName(soup, product),
                                           self._setProductSizes(soup, product),
                                           self._setProductPrice(soup, product),
                                           self._setProductThumbUrl(soup, product),
                                           self._setProductReleaseTime(soup, product))
            # Product completed
            product.setLastScanNow()
            logger.debug("Completed product %s", product.url)
            # Process things that have to be done when we got updated data for the product
            if True in results:
                self._scrapeeRepo.update(shop=self._scrapee)
                await self.sendMessage(productMsg=product, shop=self._scrapee)

    @staticmethod
    def _processSizeChange(product: Product,
                           sizeStr: str,
                           isSizeInStock: bool) -> ProductChanged:

        isProductChanged = False

        # Check if scraped size already exists
        foundSize: Size = product.findSize(sizeStr)

        # If an existing size was found, copy its reference(!). Otherwise, take a new Size object.
        size: Size = foundSize if foundSize else Size()

        # 1.
        # Scraped size does not exist at all, so add to product and mark product as changed.
        if not foundSize:
            size.sizeEU = sizeStr
            product.addSize(size=size)
            isProductChanged = True
            logger.debug("New size '%s' detected & added. %s", size.sizeEU, product.url)

        # 2.
        # Size already exists but its stock indicator is marked as unavailable, whereas the
        # newly scraped size is marked as in-stock. Mark product as changed.
        if not size.isInStock and isSizeInStock:
            isProductChanged = True
            logger.debug("Size '%s' has been restocked. %s", size.sizeEU, product.url)

        # 3.
        # After comparison, set/update size stock indicator. Always update ALL
        # found sizes as their availability may have changed to True or False and
        # we have to be up-to-date in case we are sending a message.
        # Note that 'size' var whether is a yet unrelated Size object or a reference
        # to an existing product.size
        size.isInStock = isSizeInStock

        return isProductChanged

    @abstractmethod
    async def _setShopName(self, soup: BeautifulSoup) -> ShopChanged:
        isShopChanged = False

        try:
            # Do not overwrite name if already exists
            if not self._scrapee.name:
                self._scrapee.name = soup.title.text.strip()
                isShopChanged = True

            else:
                logger.debug("Shop name exists, won't overwrite '%s'. %s",
                             self._scrapee.name, self._scrapee.url)

        except (TypeError, ValueError, AttributeError) as e:
            logger.warning("Failed parsing shop name for %s: %s", self._scrapee.url, e)
            self._failCount += 1

        else:
            logger.debug("Found shop name '%s'. %s", self._scrapee.name, self._scrapee.url)

        finally:
            return isShopChanged

    @abstractmethod
    async def _setProductName(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        ...

    @abstractmethod
    async def _setProductSizes(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        ...

    @abstractmethod
    async def _setProductPrice(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        ...

    @abstractmethod
    async def _setProductThumbUrl(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        ...

    @abstractmethod
    async def _setProductReleaseTime(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        ...