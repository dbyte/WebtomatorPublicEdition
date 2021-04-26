# shop.productsUrlsRepo.py
from __future__ import annotations

import urllib.parse as urlparse
from typing import TYPE_CHECKING

import debug.logger as clog
from shop.productsUrlsDao import ProductsUrlsDao
from shop.shop import Shop

if TYPE_CHECKING:
    from typing import Optional, List
    from storage.base import Dao
    from shop.product import Product

logger = clog.getLogger(__name__)


class ProductsUrlsRepo:

    def __init__(self, dao: Dao = ProductsUrlsDao()):
        self._dao = dao

    def getAll(self) -> Optional[List[Product]]:
        with self._dao as dao:
            products: List[Product] = dao.loadAll()  # raises
        return products

    def createShops(self) -> Optional[List[Shop]]:
        try:
            products: List[Product] = self.getAll()  # raises

        except Exception as e:
            raise LookupError("No URLs for products found. Check your ProductsURLs "
                              f"repository file. {e}")

        if not products:
            return None

        shops: List[Shop] = list()
        shopsNetlocs: List[str] = list()
        assignedProducts: List[Product] = list()

        for product in reversed(products):
            if product in assignedProducts: continue

            try:
                urlParts = urlparse.urlparse(url=product.url)
                productUrlScheme = urlParts.scheme
                productNetloc = urlParts.netloc

            except Exception as e:
                raise ValueError(f"URL could not be parsed into parts. {e}")

            if not productUrlScheme or not productNetloc:
                continue

            if productNetloc in shopsNetlocs:
                # Shop for this product already created, skip
                continue

            else:
                # Create shop.
                # Note: Leave shop.name empty, so it has a chance to become set by scraping.
                shopsNetlocs.append(productNetloc)
                shopURL = urlparse.urlunparse((productUrlScheme, productNetloc, '', '', '', ''))
                shop = Shop(url=shopURL)
                assignedProducts.extend(shop.assignProducts(products))
                shops.append(shop)

        if shops:
            return shops
        else:
            return None
