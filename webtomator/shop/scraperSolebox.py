# shop.scraperSolebox.py
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import debug.logger as clog
from network.connection import Tools
from shop.scraper import ShopScraper, ProductChanged, ShopChanged

if TYPE_CHECKING:
    from typing import ClassVar
    from bs4 import BeautifulSoup

    import network.messenger as msn
    from network.connection import Request
    from shop.product import Product
    from shop.shop import Shop
    from shop.shopRepo import ShopRepo

logger = clog.getLogger(__name__)


# TODO unit tests
class SoleboxShopScraper(ShopScraper):
    URL: ClassVar[str] = "https://www.solebox.com"

    def __init__(self,
                 scrapee: Shop,
                 scrapeeRepo: ShopRepo,
                 request: Request,
                 messenger: msn.Discord):

        super().__init__(scrapee=scrapee,
                         scrapeeRepo=scrapeeRepo,
                         request=request,
                         messenger=messenger)

    async def _setShopName(self, soup: BeautifulSoup) -> ShopChanged:
        return await super()._setShopName(soup=soup)

    async def _setProductName(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        isProductChanged = False

        try:
            nameElem = soup.find("div", class_="js-product-details")
            jsonProductDetails = nameElem.attrs.get("data-gtm", "")
            dictProductDetails = json.loads(jsonProductDetails)
            name = dictProductDetails.get("name")

        except AttributeError as e:
            logger.warning("Failed finding product name. %s %s", e, product.url)
            self._failCount += 1

        else:
            logger.debug("Found product name '%s' for %s", name, product.url)
            if not product.name or product.name != name:
                product.name = name
                isProductChanged = True  # note that we never switch back to False

        finally:
            return isProductChanged

    async def _setProductSizes(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        # Marks that at minimum one size of that product was out of stock
        # or not listed at all, but now is in stock.
        isProductChanged = False

        try:
            allSizes = set(soup.select("span.js-size-value"))
            soldOutSizes1 = set(soup.select("span.js-size-value.b-swatch-value--in-store-only"))
            soldOutSizes2 = set(soup.select("span.js-size-value.b-swatch-value--sold-out"))
            soldOutSizes = soldOutSizes1.union(soldOutSizes2)
            availableSizes = allSizes - soldOutSizes

        except (TypeError, KeyError, ValueError):
            self._failCount += 1
            logger.warning("Failed finding HTML code for sizes. %s", product.url)

        except Exception as e:
            self._failCount += 1
            logger.error("%s while searching HTML code for sizes. %s",
                         Tools.getTypeString(e), product.url, exc_info=True)

        else:
            allSizes = sorted([e.text.strip() for e in allSizes])
            availableSizes = sorted([e.text.strip() for e in availableSizes])

            for scrapedSizeStr in allSizes:
                isScrapedInStock = scrapedSizeStr in availableSizes

                isSizeChanged = self._processSizeChange(
                    product=product, sizeStr=scrapedSizeStr, isSizeInStock=isScrapedInStock)

                # Note that we never switch back to False!
                if not isProductChanged:
                    isProductChanged = isSizeChanged

        return isProductChanged

    async def _setProductPrice(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        isProductChanged = False

        try:
            thisProductInfo = soup.find("div", class_="b-pdp-product-info-section")
            priceElem = thisProductInfo.find("span", class_="b-product-tile-price-item")
            priceAndCurrencyStr = priceElem.text.strip()  # like '98,55 €'
            # Split price and currency
            match = re.search(r"(([0-9.,]+)\s+([^0-9]+))", priceAndCurrencyStr)
            priceStr, currencyStr = match.group(2), match.group(3)
            priceFloat = float(priceStr.replace(",", "."))

        except Exception as e:
            logger.warning("Failed finding product price or currency. %s. %s", e, product.url)
            self._failCount += 1

        else:
            logger.debug("Extracted product price & currency from HTML code. %s", product.url)
            if not product.basePrice or product.basePrice != priceFloat:
                product.basePrice = priceFloat
                product.currency = currencyStr
                isProductChanged = True  # note that we never switch back to False

        finally:
            return isProductChanged

    async def _setProductThumbUrl(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        isProductChanged = False

        try:
            urlThumb = soup.find("div", {"class": "b-pdp-product-preview-wrapper"}) \
                .find("div", {"class": "b-pdp-carousel-item"}) \
                .div["data-default-src"]

            if not urlThumb: raise AttributeError("No matches in HTML tree.")

        except AttributeError as e:
            logger.warning("Failed finding product image url. %s. %s", e, product.url)
            self._failCount += 1

        else:
            logger.debug("Found product image url. %s", product.url)
            if not product.urlThumb or product.urlThumb != urlThumb:
                product.urlThumb = urlThumb
                isProductChanged = True  # note that we never switch back to False

        finally:
            return isProductChanged

    # TODO
    async def _setProductReleaseTime(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        isProductChanged = False
        return isProductChanged
