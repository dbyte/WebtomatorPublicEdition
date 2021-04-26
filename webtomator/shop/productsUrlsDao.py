# shop.productsUrlsDao.py

import pathlib as pl
from typing import Optional, ClassVar, List

import debug.logger as clog
from config.base import APP_USERDATA_DIR
from shop.product import DictProductsUrlsConverter, Product
from storage.fileDao import TextFileDao

logger = clog.getLogger(__name__)


class ProductsUrlsDao(TextFileDao):
    """ Manages access to a persistent global collection of all URLs for all
    products - in a text file which we treat like a database.
    """
    _DEFAULT_PATH: ClassVar = APP_USERDATA_DIR / "ProductsURLs.txt"

    def __init__(self, filepath: pl.Path = None):
        path = filepath or self._DEFAULT_PATH
        super().__init__(path)

    def loadAll(self) -> Optional[List[Product]]:
        urlDict = super().loadAll()  # raises

        converter = DictProductsUrlsConverter(source=urlDict, target=List[Product])
        return converter.getConverted()

    def saveAll(self, data: List[Product] = None) -> None:
        if not isinstance(data, list): return
        if not all(isinstance(i, Product) for i in data):
            raise TypeError(
                "Failed saving product URLs. Given data must be of type List[Product]")

        # Convert product object list to dict...
        converter = DictProductsUrlsConverter(source=data, target=dict)
        dataDict = converter.getConverted()
        # ... and further to a flat string list
        urls: list = dataDict.get(DictProductsUrlsConverter.URL_RECORDS_KEY)

        if urls:
            # Convert string list to a newline-separated string
            dataText = "\n".join(urls)

            # Finally persist the generated string
            super().saveAll(data=dataText)

    def update(self, data):
        raise NotImplementedError

    def find(self, **kwargs):
        raise NotImplementedError

    # 1.
    def _cleanupRecord(self, record: str) -> Optional[str]:
        logger.debug("Before cleanup: %s", record.replace("\n", "\\n"))
        tmp = super()._cleanupRecord(record)  # Removes newlines
        if not tmp: return None
        tmp = tmp.strip()  # Removes all whitespace
        logger.debug("After cleanup: %s", tmp)
        return tmp if tmp else None

    # 2.
    def _filterRecord(self, record: str) -> Optional[str]:
        if record.startswith("#"):
            logger.debug("Record will be filtered out: %s", record)
            return None
        return record

    # 3.
    def _verifyRecord(self, record: str) -> bool:
        logger.debug("Verifying record: %s", record)
        if record.startswith("http"):
            return True
        else:
            logger.warning("Invalid record. No http part detected: %s", record)
        return False
