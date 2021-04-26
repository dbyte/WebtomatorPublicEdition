# shop.shop.py
import debug.logger as clog
import urllib.parse as urlparse
from typing import List

from scraper.base import Scrapable
from shop.product import Product
from storage.base import Identifiable

logger = clog.getLogger(__name__)


class Shop(Identifiable, Scrapable):
    """ A scrapable shop.
    """
    def __init__(self, **kwargs):
        self.__uid: str = kwargs.get("uid", self.generateUID())
        self.__name: str = kwargs.get("name", "")
        self.__url: str = kwargs.get("url", "")
        self.__products: List[Product] = kwargs.get("products", list())
        self.__lastScanStamp: float = 0.0

    def __repr__(self):
        info = f"<{self.__class__.__name__} uid: {self.uid}, name: {self.name}, " \
               f"url: {self.url}, lastScanStamp: {self.lastScanStamp}, products: {self.products}" \
               ">"
        return info

    def __eq__(self, other):
        return self.__repr__() == other.__repr__()

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
    def url(self, val) -> None:
        self.__url = val

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, val) -> None:
        self.__name = val

    @property
    def lastScanStamp(self) -> float:
        return self.__lastScanStamp

    @lastScanStamp.setter
    def lastScanStamp(self, val: float) -> None:
        self.__lastScanStamp = val

    @property
    def products(self) -> List[Product]:
        """ List of all product objects of this shop.
        """
        return self.__products

    @products.setter
    def products(self, productList: List[Product]) -> None:
        if not productList: return
        # Type checking
        if all(isinstance(i, Product) for i in productList):
            self.__products = productList
        else:
            raise TypeError(
                "Could not set the shop's product list. All elements must be of type 'Product'.")

    def addProduct(self, product: Product) -> None:
        """ Add a product to the shop's products list.
        Note: A product with the same URL of an already listed product won't be added. This
        would be logged at INFO level.

        :param product: Product to be added
        :return: None
        """
        # Type checking
        if not isinstance(product, Product):
            raise TypeError(f"Could not add product {product} to shop. It must be an "
                            "instance of 'Product'")

        urlDubs = len(list(filter(lambda p: p.url == product.url, self.__products)))
        if urlDubs == 0:
            self.__products.append(product)
            logger.debug("Product added to shop '%s': %s", self.name, repr(product))
        else:
            logger.info("Product not added to shop, it's already registered: %s",
                        repr(product))

    def removeProduct(self, product: Product) -> None:
        """ Remove a product from the shop's products list

        :param product: Product to be removed
        :return: None
        :raises: TypeError
        """
        # Type checking
        if not isinstance(product, Product):
            raise TypeError(f"Could not remove product {product} from shop. It must be an "
                            "instance of 'Product'")

        if product in self.__products:
            self.__products.remove(product)
            logger.debug("Product removed from shop '%s': %s", self.name, repr(product))

    def getNetloc(self) -> str:
        """Returns netloc of the shop's URL, as of:
        <scheme>://<netloc>/<path>?<query>#<fragment>

        :return: The netloc part of an URL
        :raises: ValueError
        """
        if not self.url: return ""
        parsed: urlparse.SplitResult = urlparse.urlsplit(self.url)
        if not parsed.netloc:
            raise ValueError(f"Could not find netloc part of URL {self.url}")

        return parsed.netloc

    def assignProducts(self, products: List[Product]) -> List[Product]:
        """ Adds products to this shop which have the same netloc as the url of this shop.
        Products which are already assigned won't be added as implied in self.addProduct().

        :param products: All registered products, no matter which shop they belong to
        :return: A list of all added product objects. Empty list if none was added.
        """
        matchingProducts: List[Product] = list()

        if not products:
            return matchingProducts

        for product in products:
            netloc = urlparse.urlsplit(product.url).netloc
            if netloc == self.getNetloc():
                self.addProduct(product)
                matchingProducts.append(product)

        return matchingProducts