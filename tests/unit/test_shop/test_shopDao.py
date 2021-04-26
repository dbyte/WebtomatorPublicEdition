# unit.test_shop.test_shopDao.py
from unittest.mock import Mock

import tinydb as tdb

from fixtures.shop import TEMP_SHOPS_TINYDB_TEST_PATH, ShopFixture
from shop.shop import Shop
from shop.shopDao import TinyShopDao
from unit.testhelper import WebtomatorTestCase


class TinyShopDaoTest(WebtomatorTestCase):
    testDBPath = TEMP_SHOPS_TINYDB_TEST_PATH

    def setUp(self) -> None:
        # Creates new DB at given path if not exists.
        # Deletes all records in all tables if DB exists.
        dbRef = tdb.TinyDB(str(self.testDBPath))
        dbRef.purge_tables()
        dbRef.close()

    def tearDown(self) -> None:
        pass

    def test_saveAll(self):
        # Given
        assert self.testDBPath.exists()  # Precondition for the test
        fixture = ShopFixture()
        fixture.create2Shops()

        # When
        with TinyShopDao(self.testDBPath) as sut:
            sut.saveAll(data=fixture.shops)

        # Then
        # Expect that DB still exists
        self.assertTrue(self.testDBPath.exists())
        # Get a ref to the DB for further tests
        dbRef = tdb.TinyDB(str(self.testDBPath))
        shopsTable: tdb.database.Table = dbRef.table(TinyShopDao._TABLE_NAME)

        # Expect that 'Shops' table has 2 records
        self.assertEqual(2, shopsTable.count(cond=lambda x: True))

        # 1st SHOP
        # ------------------------------------------------------------------------
        # Expect that the first shop's attribute values are correct
        self.assertEqual("73f9cac8-ebdc-4d9b-8163-d04d09f06cd9",
                         shopsTable.get(doc_id=1).get("uid"))
        self.assertEqual("Bottle shop", shopsTable.get(doc_id=1).get("name"))
        self.assertEqual("http://oneshop.com/bottles", shopsTable.get(doc_id=1).get("url"))

        # Expect that the first shop has a list of products
        products = shopsTable.get(doc_id=1).get("products")
        self.assertIsInstance(products, list)
        # Expect that the first shop has 2 products
        self.assertEqual(2, len(products))

        # 1st SHOP, 1st Product
        # ------------------------------------------------------------------------
        # Expect correct values of the first product
        product = products[0]
        self.assertEqual("2857027b-cf25-4639-965e-0e22f9f4c755", product.get("uid"))
        self.assertEqual("Biggest Corona Bottle ever", product.get("name"))
        self.assertEqual("http://oneshop.com/bottles/92743867ACTFGJ-UTU", product.get("url"))
        self.assertEqual(None, product.get("urlThumb"))
        self.assertEqual(55.49, product.get("basePrice"))
        self.assertEqual(1588548868.304869, product.get("lastScanStamp"))
        self.assertEqual(1601466659.0, product.get("releaseDateStamp"))

        # Expect correct sizes of the first product
        sizes = product.get("sizes")
        self.assertEqual(2, len(sizes))

        size = sizes[0]
        self.assertEqual("1528dae6-188f-4d7e-8a6c-5af44ce5c222", size.get("uid"))
        self.assertEqual("40 1/3", size.get("sizeEU"))
        self.assertEqual(56.99, size.get("price"))
        self.assertEqual("http://oneshop.com/bottles/92743867ACTFGJ-UTU/40.1.3.htm",
                         size.get("url"))
        self.assertEqual("http://oneshop.com/bottles/atc/40.1.3-92743867ACTFGJ-UTU.htm",
                         size.get("urlAddToCart"))
        self.assertEqual(True, size.get("isInStock"))

        size = sizes[1]
        self.assertEqual("5f561c62-8502-4ec1-8f46-f0adb5e8254c", size.get("uid"))
        self.assertEqual("43", size.get("sizeEU"))
        self.assertEqual(54.99, size.get("price"))
        self.assertEqual("http://oneshop.com/bottles/92743867ACTFGJ-UTU/43.htm",
                         size.get("url"))
        self.assertEqual("http://oneshop.com/bottles/atc/43-92743867ACTFGJ-UTU.htm",
                         size.get("urlAddToCart"))
        self.assertEqual(False, size.get("isInStock"))

        # 1st SHOP, 2nd Product
        # ------------------------------------------------------------------------
        # Expect correct values of the second product
        product = products[1]
        self.assertEqual("9cab557a-419a-4883-8287-f09f7244b225", product.get("uid"))
        self.assertEqual("Neck Bottle", product.get("name"))
        self.assertEqual("http://oneshop.com/bottles/1362836400447GT-UTU", product.get("url"))
        self.assertEqual(None, product.get("urlThumb"))
        self.assertEqual(3.22, product.get("basePrice"))
        self.assertEqual(1588548911.230381, product.get("lastScanStamp"))
        self.assertEqual(1675089635.0, product.get("releaseDateStamp"))
        # Expect that the second product has an empty sizes list
        sizes = product.get("sizes")
        self.assertIsInstance(sizes, list)
        self.assertEqual(0, len(sizes))

        # 2nd SHOP
        # ------------------------------------------------------------------------
        # Expect that the second shop's attribute values are correct
        self.assertEqual("69ec8e1b-8812-4413-ad72-b74364e2fa7a",
                         shopsTable.get(doc_id=2).get("uid"))
        self.assertEqual("Megashop", shopsTable.get(doc_id=2).get("name"))
        self.assertEqual("https://www.megashop.com/shoes", shopsTable.get(doc_id=2).get("url"))

        # 2nd SHOP, 1st Product
        # ------------------------------------------------------------------------
        # Expect that the second shop has a list of products
        products = shopsTable.get(doc_id=2).get("products")
        self.assertIsInstance(products, list)
        # Expect that the second shop has 1 product
        self.assertEqual(1, len(products))

        # Expect correct values of the first product
        product = products[0]
        self.assertEqual("f0700293-693c-48a6-8f01-014e07151d99", product.get("uid"))
        self.assertEqual("Hey Bro Male", product.get("name"))
        self.assertEqual("https://www.megashop.com/shoes/9a734hd78.html", product.get("url"))
        self.assertEqual("https://www.megashop.com/shoes/thumb-9a734hd78.html",
                         product.get("urlThumb"))
        self.assertEqual(190, product.get("basePrice"))
        self.assertEqual(1588548274.102859, product.get("lastScanStamp"))
        self.assertEqual(1856674960.0, product.get("releaseDateStamp"))

        # Expect correct sizes of the first product
        sizes = product.get("sizes")
        self.assertEqual(1, len(sizes))

        size = sizes[0]
        self.assertEqual("e070b0c9-769d-4c13-a208-f7207f0970db", size.get("uid"))
        self.assertEqual("44.5", size.get("sizeEU"))
        self.assertEqual(189.5, size.get("price"))
        self.assertEqual("https://megashop.com/shoes/44.5-9a734hd78.htm",
                         size.get("url"))
        self.assertEqual("https://megashop.com/shoes/atc/44.5-9a734hd78#g89.php",
                         size.get("urlAddToCart"))
        self.assertEqual(True, size.get("isInStock"))

        # Cleanup
        dbRef.close()

    def test_loadAll(self):
        # Given
        assert self.testDBPath.exists()  # Precondition for the test

        fixture = ShopFixture()
        fixture.create2Shops()
        # Generate test-data
        sut = TinyShopDao(self.testDBPath)
        sut.connection.open()
        sut.saveAll(data=fixture.shops)

        # When
        # We use client code here for convenience to convert saved data back to
        # Shop objects, which is not perfect.
        loadedShops = sut.loadAll()

        sut.connection.close()

        # Then
        self.assertIsInstance(loadedShops, list)
        self.assertEqual(2, len(loadedShops))
        self.assertEqual(fixture.shops[0], loadedShops[0])
        self.assertEqual(fixture.shops[1], loadedShops[1])

    def test_insert(self):
        # Given
        fixture = ShopFixture()
        fixture.create2Shops()
        givenShop01 = fixture.shops[0]
        givenShop02 = fixture.shops[1]

        sut = TinyShopDao(self.testDBPath)
        sut.connection.open()

        # When
        sut.insert(data=givenShop01)
        # Then
        allShops = sut.loadAll()
        self.assertIsInstance(allShops, list)
        self.assertEqual(1, len(allShops))
        self.assertEqual(givenShop01, allShops[0])

        # When
        sut.insert(data=givenShop02)

        # Then
        # We use client code here for convenience to convert saved data back to
        # Shop objects, which is not perfect.
        allShops = sut.loadAll()

        self.assertIsInstance(allShops, list)
        self.assertEqual(2, len(allShops))
        self.assertEqual(givenShop01, allShops[0])
        self.assertEqual(givenShop02, allShops[1])

        sut.connection.close()

    def test_insert_shouldRaiseIfGivenDataHasWrongType(self):
        # Given
        invalidData = Mock(name="invalidType")

        # When / Then
        with TinyShopDao(self.testDBPath) as sut:
            with self.assertRaises(TypeError):
                sut.insert(data=invalidData)

    def test_update(self):
        # Given
        assert self.testDBPath.exists()  # Precondition for the test

        # Generate test-data with 2 shop fixtures
        fixture = ShopFixture()
        fixture.create2Shops()
        fixture.shops[1].uid = "69ec8e1b-8812-4413-ad72-b74364e2fa7a"
        with TinyShopDao(self.testDBPath) as sut:
            sut.saveAll(data=fixture.shops)

        # Data to update. Note we set reference values here, so the original fixture
        # objects get modified, which is important for later equality checks.
        expectedShop = fixture.shops[1]
        expectedShop.name = "An updated shop name"
        expectedShop.url = "https://updated-shop-url.com"
        expectedShop.products[0].name = "An updated product name"
        expectedShop.products[0].sizes[0].url = "https://updated-size.com"

        # When
        with TinyShopDao(self.testDBPath) as sut:
            sut.update(data=expectedShop)

        # Then
        # Expect that DB still exists
        self.assertTrue(self.testDBPath.exists())

        # We use client code here for convenience to convert saved data back to
        # Shop objects, which is not perfect.
        with TinyShopDao(self.testDBPath) as sut:
            savedShops = sut.loadAll()

        # Expect that the first shop has been left untouched.
        self.assertEqual(fixture.shops[0], savedShops[0])
        # Expect that the second shop has been updated with correct updated values.
        self.assertEqual(fixture.shops[1], savedShops[1])

    def test_update_shouldRaiseIfGivenDataHasWrongType(self):
        # Given
        invalidData = Mock(name="invalidType")

        # When / Then
        with TinyShopDao(self.testDBPath) as sut:
            with self.assertRaises(TypeError):
                sut.update(data=invalidData)

    def test_find_shouldRaiseOnWrongKeywords(self):
        # Given

        # When / Then
        with TinyShopDao(self.testDBPath) as sut:
            with self.assertRaises(KeyError):
                sut.find(invalidKeyword="Value does not matter here")

    def test_find_uid(self):
        # Given
        # Generate test-data from 2 shop fixtures
        fixture = ShopFixture()
        fixture.create2Shops()
        expectedShop = fixture.shops[1]
        expectedUID = fixture.shops[1].uid  # UID of second fixture shop
        with TinyShopDao(self.testDBPath) as dao:
            dao.saveAll(data=fixture.shops)

        # When
        with TinyShopDao(self.testDBPath) as sut:
            foundShop = sut.find(uid=expectedUID)

        # Then
        self.assertIsInstance(foundShop, Shop)
        self.assertEqual(expectedShop, foundShop)

    def test_find_name(self):
        # Given
        # Generate test-data from 2 shop fixtures
        fixture = ShopFixture()
        fixture.create2Shops()
        expectedShop = fixture.shops[0]
        expectedShopName = fixture.shops[0].name  # shop name of second fixture shop
        with TinyShopDao(self.testDBPath) as dao:
            dao.saveAll(data=fixture.shops)

        # When
        with TinyShopDao(self.testDBPath) as sut:
            foundShops = sut.find(shopName=expectedShopName)

        # Then
        self.assertIsInstance(foundShops, list)
        self.assertEqual(1, len(foundShops))
        self.assertIsInstance(foundShops[0], Shop)
        self.assertEqual(foundShops, [expectedShop])
