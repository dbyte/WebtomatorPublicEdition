# fixtures.shop.py
import datetime as dtt
import uuid
from pathlib import Path
from typing import List

from shop.product import Size, Product
from shop.shop import Shop

__MY_ROOT = Path(__file__).parent

TEST_USERDATA_DIR_PATH = Path(__MY_ROOT, "../resources/userdata")
assert TEST_USERDATA_DIR_PATH.is_dir()

assert Path(TEST_USERDATA_DIR_PATH, "shops").is_dir()
TEMP_SHOPS_TINYDB_TEST_PATH = TEST_USERDATA_DIR_PATH / "shops/TinyDB_TempShops.json"

PRODUCTS_URLS_TEST_DIR: Path = TEST_USERDATA_DIR_PATH / "products_urls"
assert Path(TEST_USERDATA_DIR_PATH, "products_urls").is_dir()
PRODUCTS_URLS_9_VALID_TEST_PATH: Path = PRODUCTS_URLS_TEST_DIR / "ProductsURLs_9_Valid_Test.txt"
PRODUCTS_URLS_0_VALID_TEST_PATH: Path = PRODUCTS_URLS_TEST_DIR / "ProductsURLs_0_Valid_Test.txt"
PRODUCTS_URLS_INTEGRATION_TEST_PATH: \
    Path = PRODUCTS_URLS_TEST_DIR / "ProductsURLs_integrationTests.txt"


class ShopFixture:

    def __init__(self):
        self.shops: List[Shop] = list()

    def create2Shops(self) -> None:
        """ Caution: Do not change values as they are tested against
        :return: None
        """
        size01 = Size()
        size01.uid = str(uuid.UUID(hex="1528dae6-188f-4d7e-8a6c-5af44ce5c222", version=4))
        size01.sizeEU = "40 1/3"
        size01.isInStock = True
        size01.price = 56.99
        size01.url = "http://oneshop.com/bottles/92743867ACTFGJ-UTU/40.1.3.htm"
        size01.urlAddToCart = "http://oneshop.com/bottles/atc/40.1.3-92743867ACTFGJ-UTU.htm"

        size02 = Size()
        size02.uid = str(uuid.UUID(hex="5f561c62-8502-4ec1-8f46-f0adb5e8254c", version=4))
        size02.sizeEU = "43"
        size02.isInStock = False
        size02.price = 54.99
        size02.url = "http://oneshop.com/bottles/92743867ACTFGJ-UTU/43.htm"
        size02.urlAddToCart = "http://oneshop.com/bottles/atc/43-92743867ACTFGJ-UTU.htm"

        size03 = Size()
        size03.uid = str(uuid.UUID(hex="e070b0c9-769d-4c13-a208-f7207f0970db", version=4))
        size03.sizeEU = "44.5"
        size03.isInStock = True
        size03.price = 189.50
        size03.url = "https://megashop.com/shoes/44.5-9a734hd78.htm"
        size03.urlAddToCart = "https://megashop.com/shoes/atc/44.5-9a734hd78#g89.php"

        product01 = Product()
        product01.uid = str(uuid.UUID(hex="2857027b-cf25-4639-965e-0e22f9f4c755", version=4))
        product01.url = "http://oneshop.com/bottles/92743867ACTFGJ-UTU"
        product01.name = "Biggest Corona Bottle ever"
        product01.setReleaseDate(dtt.datetime(2020, 9, 30, 13, 50, 59), timezone="Europe/Berlin")
        product01.basePrice = 55.49
        product01.lastScanStamp = 1588548868.304869  # setLastScanNow()
        product01.sizes = [size01, size02]

        product02 = Product()
        product02.uid = str(uuid.UUID(hex="9cab557a-419a-4883-8287-f09f7244b225", version=4))
        product02.url = "http://oneshop.com/bottles/1362836400447GT-UTU"
        product02.name = "Neck Bottle"
        product02.setReleaseDate(dtt.datetime(2023, 1, 30, 15, 40, 35), timezone="Europe/Berlin")
        product02.basePrice = 3.22
        product02.lastScanStamp = 1588548911.230381  # setLastScanNow()
        product02.sizes = []

        product03 = Product()
        product03.uid = str(uuid.UUID(hex="f0700293-693c-48a6-8f01-014e07151d99", version=4))
        product03.url = "https://www.megashop.com/shoes/9a734hd78.html"
        product03.urlThumb = "https://www.megashop.com/shoes/thumb-9a734hd78.html"
        product03.name = "Hey Bro Male"
        product03.setReleaseDate(dtt.datetime(2028, 11, 1, 8, 2, 40), timezone="Europe/Berlin")
        product03.basePrice = 190
        product03.lastScanStamp = 1588548274.102859  # setLastScanNow()
        product03.sizes = [size03]

        shop01 = Shop()
        # ID is usually set by the DBMS, we explicitly set it for equality checks, too:
        shop01.uid = str(uuid.UUID(hex="73f9cac8-ebdc-4d9b-8163-d04d09f06cd9", version=4))
        shop01.name = "Bottle shop"
        shop01.url = "http://oneshop.com/bottles"
        shop01.products = [product01, product02]

        shop02 = Shop()
        # ID is usually set by the DBMS, we explicitly set it for equality checks, too:
        shop02.uid = str(uuid.UUID(hex="69ec8e1b-8812-4413-ad72-b74364e2fa7a", version=4))
        shop02.name = "Megashop"
        shop02.url = "https://www.megashop.com/shoes"
        shop02.products = [product03]

        self.shops = [shop01, shop02]
