# shop.product.py
import datetime as dtt
import urllib.parse as urlparse
from typing import Optional, Union, ClassVar, List

import pytz

import debug.logger as clog
from scraper.base import Scrapable
from storage.base import Identifiable
from story.baseConverter import BaseConverter

logger = clog.getLogger(__name__)


class Product(Identifiable, Scrapable):
    """ Product class.

    Note: All date/datetime data in this class are stored as UTC and UNIX timestamp (float) format.
    """
    def __init__(self, **kwargs):
        self.__uid: str = kwargs.get("uid", self.generateUID())
        self.__name: str = kwargs.get("name", "")
        self.__url: str = kwargs.get("url", "")
        self.basePrice: Optional[float] = kwargs.get("basePrice", None)
        self.currency: Optional[str] = kwargs.get("currency", None)
        self.__sizes: [Size] = kwargs.get("sizes", list())
        self.urlThumb: Optional[str] = kwargs.get("urlThumb", None)
        self.__releaseDateStamp: Optional[float] = kwargs.get("releaseDateStamp", None)  # **
        self.__lastScanStamp: float = kwargs.get("lastScanStamp", 0.0)  # **

        # ** is of format UTC UNIX epoch

    def __repr__(self):
        info = f"<{self.__class__.__name__} uid: {self.uid}, name: {self.name}, " \
               f"url: {self.url}, price: {self.basePrice}, currency: {self.currency}, " \
               f"sizes: {self.__sizes}, urlThumb: {self.urlThumb}, " \
               f"releaseDateStamp: {self.__releaseDateStamp}, " \
               f"lastScanStamp: {self.lastScanStamp}" \
               ">"

        return info

    @property
    def uid(self) -> str:
        return self.__uid

    @uid.setter
    def uid(self, val: str) -> None:
        self.__uid = val

    @property
    def url(self) -> str:
        return self.__url

    @url.setter
    def url(self, val: str) -> None:
        self.__url = val

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, val: str) -> None:
        self.__name = val

    @property
    def lastScanStamp(self) -> float:
        return self.__lastScanStamp

    @lastScanStamp.setter
    def lastScanStamp(self, val: float) -> None:
        self.__lastScanStamp = val

    @property
    def sizes(self) -> List['Size']:
        return self.__sizes

    @sizes.setter
    def sizes(self, sizeList: List['Size']) -> None:
        if not sizeList: return
        # Type checking
        if all(isinstance(i, Size) for i in sizeList):
            self.__sizes = sizeList
        else:
            raise TypeError("Could not set sizes list. All elements must be of type 'Size'.")

    def addSize(self, size: 'Size') -> None:
        """ Adds a size to the product's list of sizes.

        :param size: An instance of type Size.
        :type size: Size
        :return: None
        """
        if not isinstance(size, Size):
            raise TypeError("Could not add size. Expected an instance of type 'Size' "
                            f"but got {type(size)}")

        if size:
            self.sizes.append(size)
            logger.debug("Added new size %s for %s", size.sizeEU, self.url)

    def findSize(self, sizeStr: str) -> Optional['Size']:
        """ Find and return a Size with the given size string.

        :param sizeStr: Complete size string to search for.
        :return: Size object if found, otherwise None
        """
        for size in self.sizes:
            if size.sizeEU == sizeStr:
                logger.debug("Found existing size %s for %s", sizeStr, self.url)
                # Size exists. Return reference(!) of product.size
                return size
        return None

    @property
    def releaseDateStamp(self) -> Optional[float]:
        """
        :return: The internally stored UNIX epoch timestamp as float OR None if not set.
        """
        return self.__releaseDateStamp

    def invalidateReleaseDate(self) -> None:
        """ Sets release date back to None.
        :return: None
        """
        self.__releaseDateStamp = None

    def getReleaseDate(self, forTimezone: str, forType: type) -> \
            Optional[Union[str, dtt.datetime]]:
        """Returns the release date and time for the product when there is one - else returns None.

        :param forType: Pass type 'str' for human readable return; pass type 'datetime' for
                        python datetime. Unknown types will raise a NotImplementedError.
        :param forTimezone: Timezone string for the returned release date. Raises
                            error on invalid time zone. For a list of valid strings,
                            see 'pytz.all_timezones'
        :return: None when no release date is set.
                 Else a timezone aware datetime or a readable string.
        """
        if not self.__releaseDateStamp:
            return None

        allowedTypes = (str, dtt.datetime)
        if forType not in allowedTypes:
            raise NotImplementedError(f"Given type '{forType}' is not allowed as an output type.")

        # Return formatted local date/time string
        if forType is str:
            try:
                localDatetime = self.__releaseStampToLocalDatetime(forTimezone)
                result = dtt.datetime.strftime(localDatetime, "%d.%m.%Y, %H:%M:%S")
                return result
            except pytz.UnknownTimeZoneError:
                raise

        # Return local datetime
        elif forType is dtt.datetime:
            try:
                return self.__releaseStampToLocalDatetime(forTimezone)
            except pytz.UnknownTimeZoneError:
                raise

    def setReleaseDate(self, datetime: dtt.datetime, timezone: str) -> None:
        """ Set the release date for the product providing a Python datetime.

        :param datetime: Python datetime (without any timezone info).
                         You must define the timezone in param 'timezone'!
        :param timezone: Timezone string, see also 'pytz.all_timezones'
        :return: None
        """
        try:
            if not timezone:
                raise pytz.UnknownTimeZoneError("No timezone given.")

            givenZone = pytz.timezone(timezone)  # set the source's timezone
            localizedDatetime = givenZone.localize(datetime)  # make source timezone-aware
            datetimeUTC: dtt.datetime = localizedDatetime.astimezone(pytz.utc)  # convert to UTC

        except pytz.UnknownTimeZoneError as e:
            logger.error("Could not set product release date. Invalid time zone string. %s", e,
                         exc_info=True)

        except Exception as e:
            logger.error("Could not set product release date. %s", e, exc_info=True)

        else:
            self.__releaseDateStamp = datetimeUTC.timestamp()

    def getPriceWithCurrency(self) -> str:
        if self.basePrice and self.currency:
            return "{:.2f} {:s}".format(self.basePrice, self.currency)
        elif self.basePrice:
            return "{:.2f} [UNKNOWN CURRENCY]".format(self.basePrice)
        else:
            return "unknown"

    def __releaseStampToLocalDatetime(self, forTimezone: str) -> Optional[dtt.datetime]:
        """ Result is a so called AWARE datetime with the given timezone - which means that
        the offset to the UTC is included in the result.
        Ex.: A result 2035-07-15 12:55:00+02:00 says:
        1) Local time is 12:55:00 and
        2) the offset to the UTC is +2 hours, so UTC for this local is 10:55:00.

        Raises on invalid timezone string!

        :param forTimezone: Timezone string for the returned release date. Raises
                            error on invalid time zone. For a list of valid strings,
                            see 'pytz.all_timezones'
        :return: None when no release date is set. Else a timezone aware datetime.
        """
        pytzGivenZone = pytz.timezone(forTimezone)  # raises on invalid timezone string!
        utcDatetime = dtt.datetime.utcfromtimestamp(self.__releaseDateStamp)  # get as datetime
        utcAwareDatetime = pytz.utc.localize(utcDatetime)  # make timezone-aware
        localAwareDatetime = utcAwareDatetime.astimezone(pytzGivenZone)  # convert to given zone

        return localAwareDatetime


class Size(Identifiable):

    def __init__(self, **kwargs):
        self.__uid: str = kwargs.get("uid", self.generateUID())
        # Size itself must be str for patterns like '42 2/3'. None for unknown.
        self.sizeEU: Optional[str] = kwargs.get("sizeEU", None)
        # Price None for unknown.
        self.price: Optional[float] = kwargs.get("price", None)
        # URL None for unknown.
        self.url: Optional[str] = kwargs.get("url", None)
        # addToCart url: None for unknown.
        self.urlAddToCart: Optional[str] = kwargs.get("urlAddToCart", None)
        # In stock: None for unknown. Optionals won't not work for bool (as of Py 3.7.7)
        self.isInStock: Optional[bool] = kwargs.get("isInStock", None)

    def __repr__(self):
        info = f"<{self.__class__.__name__} uid: {self.uid}, sizeEU: {self.sizeEU}, " \
               f"price: {self.price}, url: {self.url}, urlAddToCart: {self.urlAddToCart}, " \
               f"isInStock: {self.isInStock}" \
               ">"

        return info

    @property
    def uid(self) -> str:
        return self.__uid

    @uid.setter
    def uid(self, val: str) -> None:
        self.__uid = val

    @property
    def inStockReadable(self) -> str:
        # Explicitly ask for None. This is no glitch!
        if self.isInStock is None:
            return "Unknown"

        # Explicitly ask for False. This is no glitch!
        elif self.isInStock is False:
            return "Out of stock"

        # Explicitly ask for True. This is no glitch!
        elif self.isInStock is True:
            return "In stock"

        else:
            msg = "Variable 'isInStock' neither seems to be a boolean, nor a None. " \
                  f"Its type is: {type(self.isInStock)}"

            logger.critical(msg)
            raise TypeError(msg)


class StringProductUrlConverter(BaseConverter):

    def __init__(self, source, target):
        super().__init__(source, target, allowedTypes=(Product, str))

    def getConverted(self):
        if self._target == Product:
            return self.__urlStringToProduct()
        return self.__productToUrlString()

    def __urlStringToProduct(self) -> Optional[Product]:
        urlStr: str = self._source
        if not urlStr: return None

        # We'll a valid netloc to assign a product to a shop later in the app flow,
        # let's check if we get one - else raise because we consider it
        # to be an invalid product URL.
        netloc = urlparse.urlsplit(urlStr).netloc
        if not netloc:
            raise ValueError(f"URL not splittable into a valid netloc part: {urlStr}")

        newProduct = Product()
        newProduct.url = urlStr

        logger.debug("New Product created from URL string. Product URL: %s",
                     newProduct.url)

        return newProduct

    def __productToUrlString(self) -> Optional[str]:
        product: Product = self._source
        if not product or not product.url: return None

        return product.url


class DictProductsUrlsConverter(BaseConverter):
    URL_RECORDS_KEY: ClassVar = "data"  # See also TextFileDao._recordArrayKey

    def __init__(self, source, target):
        super().__init__(source, target, allowedTypes=(List[Product], dict))

    def getConverted(self) -> Union[List[Product], dict]:
        if self._target == dict:
            return self.__productsToUrlDict()
        return self.__urlDictToProducts()

    def __urlDictToProducts(self) -> [Product]:
        urlDict: dict = self._source

        if self.URL_RECORDS_KEY not in urlDict.keys():
            raise KeyError(f"Missing dictionary key '{self.URL_RECORDS_KEY}' in urlDict.")

        products: [Product] = []
        urls = urlDict.get(self.URL_RECORDS_KEY)

        for url in urls:
            if not url: continue
            converter = StringProductUrlConverter(source=url, target=Product)
            product: Product = converter.getConverted()
            if product:
                products.append(product)

        return products

    def __productsToUrlDict(self) -> dict:
        products: [Product] = self._source

        urlDict = {self.URL_RECORDS_KEY: []}

        for product in products:
            if not product: continue
            if product.url:
                urlDict[self.URL_RECORDS_KEY].append(product.url)

        return urlDict
