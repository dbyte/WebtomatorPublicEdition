# shop.scraperBstn.py
from __future__ import annotations

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
class BstnShopScraper(ShopScraper):
    URL: ClassVar[str] = "https://www.bstn.com"

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
            nameElem = soup.find("div", id="detailRight")
            name = nameElem.find("span", class_="productname").get_text(strip=True)
            if not name: raise ValueError("HTML elements not found.")

        except (ValueError, AttributeError) as e:
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
            elem = soup.find("div", class_="edd-dropdown clear")
            allSizes = set(elem.findAll("option"))
            availableSizes = set(elem.findAll("option", {"class": ""}))
            ignorableElements = set(elem.findAll("option", {"class": None}))
            allSizes = allSizes.difference(ignorableElements)
            availableSizes = availableSizes.difference(ignorableElements)
            if not allSizes: raise ValueError("No matches in HTML tree.")

        except (TypeError, KeyError, ValueError) as e:
            self._failCount += 1
            logger.warning("Failed finding HTML code for sizes. %s %s", e, product.url)

        except Exception as e:
            self._failCount += 1
            logger.error("%s while searching HTML code for sizes. %s",
                         Tools.getTypeString(e), product.url, exc_info=True)

        else:
            allSizes = sorted([e.text.strip().strip("()") for e in allSizes])
            availableSizes = sorted([e.text.strip().strip("()") for e in availableSizes])

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
            elem = soup.find("div", class_="buybox").find("div", class_="price")
            priceStr = elem.find("meta", {"itemprop": "price"})["content"]
            currencyStr = elem.find("meta", {"itemprop": "pricecurrency"})["content"]
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
            urlThumb = soup.find("li", class_="thumbnail-1") \
                .find("div", class_="wrap") \
                .img["src"]

            # Below code possibly superfluous. The above urlThumb is already valid,
            # but for mighty reasons linking to it in Discord seems to get blocked by BSTN. There's
            # a way to shorten the URL, as the last parts of the URL don't seem to be relevant.
            # Anyway, this won't fix the blocked link in Discord.
            # Example
            # https://www.bstn.com/media/140801/w/280/h/280/n/adidas-zx-8000-fv3269-1.jpg
            # is converted to
            # https://www.bstn.com/media/140801/w/280/h/280/n/0.jpg
            # match = re.search(r".*/h/280/n/", urlThumb)
            # urlThumb = f"{match.group()}0.jpg"

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
