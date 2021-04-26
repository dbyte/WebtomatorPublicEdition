# shop.scraperFootdistrict.py
from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import debug.logger as clog
from network.connection import Tools
from shop.scraper import ShopScraper, ProductChanged, ShopChanged

if TYPE_CHECKING:
    from typing import ClassVar, List
    from bs4 import BeautifulSoup

    import network.messenger as msn
    from network.connection import Request
    from shop.product import Product
    from shop.shop import Shop
    from shop.shopRepo import ShopRepo

logger = clog.getLogger(__name__)


# TODO unit tests
class FootdistrictShopScraper(ShopScraper):
    URL: ClassVar[str] = "https://footdistrict.com"

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
            name = soup.find("div", {"class": "product-shop"}) \
                .find("div", {"class": "product-name"}) \
                .get_text(strip=True)

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
        jsCode = await self._getJsCodeForSizes(soup=soup, product=product)
        sizeList, isInStockList = self._extractSizeData(jsCode=jsCode, product=product)

        if not sizeList or not isInStockList:
            logger.warning("Failed getting size list or stock list for %s", product.url)
            self._failCount += 1
            return False

        # Marks that at minimum one size of that product was out of stock, but now is in stock.
        isProductChanged = False

        for scrapedSizeStr, isScrapedInStock in zip(sizeList, isInStockList):

            isSizeChanged = self._processSizeChange(
                product=product, sizeStr=scrapedSizeStr, isSizeInStock=isScrapedInStock)

            # Note that we never switch back to False!
            if not isProductChanged:
                isProductChanged = isSizeChanged

        return isProductChanged

    async def _setProductPrice(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        """ We need to find & extract price and currency from the following JS code:
        <script>
            fbq('track', 'ViewContent', {
            value: '64',
            currency: 'EUR',
            content_ids: '245134',
            content_type: 'product_group',
            });
        </script>
        """
        isProductChanged = False

        jsCodeToFind = "fbq\\(\'track\', \'AddToCart\'"
        reCompiled = re.compile(jsCodeToFind)

        try:
            javascriptStr = soup.find("script",
                                      attrs={"type": "text/javascript"},
                                      text=reCompiled).string

            priceStr = re.search(r"value:\s+(.*?)[,\n]", javascriptStr).group(1).strip("\'")
            priceFloat = float(priceStr)
            currency = re.search(r"currency:\s+(.*?)[,\n]", javascriptStr).group(1).strip("\'")

        except Exception as e:
            logger.warning("Failed finding product price or currency. %s. %s", e, product.url)
            self._failCount += 1

        else:
            logger.debug("Extracted product price & currency from JS code. %s", product.url)
            if not product.basePrice or product.basePrice != priceFloat:
                product.basePrice = priceFloat
                product.currency = currency
                isProductChanged = True  # note that we never switch back to False

        finally:
            return isProductChanged

    async def _setProductThumbUrl(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        """
        Search for the following JS code and extract URL:
        <div class="more-views mobilehidden">
           <ul>
            <li>
             <a href="https:// ...
        """
        isProductChanged = False

        try:
            urlThumb = soup.find("div", {"class": "product-img-box"}) \
                .find("div", {"class": "more-views mobilehidden"}) \
                .find_next("a").get("href")

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

    async def _setProductReleaseTime(self, soup: BeautifulSoup, product: Product) -> ProductChanged:
        isProductChanged = False

        searchString = "var countDownDate"
        reCompiled = re.compile(searchString)
        timeString = ""

        try:
            foundCode = soup.find("script",
                                  attrs={"type": "text/javascript"},
                                  text=reCompiled).string

            logger.debug("Found JS code for string '%s'. %s", searchString, product.url)

            # Regex
            pattern = "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][" \
                      "0-9]):[0-5][0-9]:[0-5][0-9]"
            match = re.search(pattern, foundCode)
            timeString = match.group(0)

            # TODO Conversion timeString to locale datetime
            # product.setReleaseDate(datetime=None, timezone=None)

        except AttributeError:
            # As release dates are rare cases, we do NOT log it as a warning but a debug.
            # Also, we do not count up self._failCount.
            logger.debug("No JS code with string '%s' found for release date. %s",
                         searchString, product.url)

        except Exception as e:
            logger.error("%s while searching JS code for release date. %s",
                         Tools.getTypeString(e), product.url, exc_info=True)

        finally:
            return isProductChanged

    @staticmethod
    async def _getJsCodeForSizes(soup: BeautifulSoup, product: Product) -> str:
        """ Searches for Javascript code which has the sizes data. If not found,
        an empty string is returned. Search for the following JS code:
        <script type="text/javascript">
            var spConfig = new Product.Config({"attributes":{"134":{ ...
        </script>
        """

        searchString = "new Product.Config"
        reCompiled = re.compile(searchString)
        foundCode = ""

        try:
            foundCode = soup.find("script",
                                  attrs={"type": "text/javascript"},
                                  text=reCompiled).string
            logger.debug("Found JS code for string '%s'. %s", searchString, product.url)

        except AttributeError as e:
            logger.warning("Failed finding JS code for sizes. %s %s", e, product.url)

        except Exception as e:
            logger.error("%s while searching JS code for sizes. %s",
                         Tools.getTypeString(e), product.url, exc_info=True)

        finally:
            return foundCode

    def _extractSizeData(self, jsCode: str, product: Product) -> (List[str], List[bool]):
        """ Extract JSON code from given JS code:
        var spConfig = new Product.Config({ ... }});
        """
        if not jsCode: return list(), list()

        # Two lists which are expected to be of same length
        sizeStrList: List[str] = list()
        isSizeInStockList: List[bool] = list()

        # Extract the JSON string from all the mess around
        match = re.search(r"[^{]*({.*\})[^\}]*", jsCode)

        if (not match) or (not match.group(1)):
            logger.warning("Could not extract JS code for sizes. %s", product.url)
            return sizeStrList, isSizeInStockList

        jsonString = match.group(1)

        try:
            data: dict = json.loads(jsonString)
            attrNode = data.get("attributes", {})
            fixedIdNode = attrNode.get("134", {})
            lineItems = fixedIdNode.get("options")

        except Exception as e:
            logger.error("%s while searching JS code for sizes. %s",
                         Tools.getTypeString(e), product.url, exc_info=True)

        else:
            if isinstance(lineItems, list):
                for item in lineItems:
                    rawSizeStr = item.get("label")
                    if rawSizeStr:
                        sizeStr = self._rawSizeStringToFinal(rawSizeStr, product)
                        if sizeStr:
                            sizeStrList.append(sizeStr)
                            isSizeInStockList.append("Not available" not in rawSizeStr)

        if sizeStrList:
            logger.debug("Process total %d sizes from JS code completed. %s",
                         len(sizeStrList), product.url)
        else:
            logger.warning("Failed finding sizes in JS code. %s", product.url)

        return sizeStrList, isSizeInStockList

    @staticmethod
    def _rawSizeStringToFinal(rawSizeStr: str, product: Product) -> str:
        """ Extract the final size string from string with a format of for example
        "37 * Not available" or "38.5 * Not available" or "39.5"
        """
        if not rawSizeStr: return ""

        finalSizeStr = ""
        try:
            floatOnly = re.search(r"[-+]?\d*\.\d+|\d+", rawSizeStr).group()
            if floatOnly:
                finalSizeStr = str(floatOnly)
                logger.debug("Completed extraction of final size string. %s", product.url)

        except Exception as e:
            logger.error("% while extracting raw size string. %",
                         Tools.getTypeString(e), product.url, exc_info=True)

        finally:
            return finalSizeStr
