# unit.test_shop.test_shopRepo.py
from unittest.mock import Mock

import tinydb as tdb

from fixtures.shop import ShopFixture, TEMP_SHOPS_TINYDB_TEST_PATH, \
    PRODUCTS_URLS_9_VALID_TEST_PATH, PRODUCTS_URLS_TEST_DIR
from shop.shop import Shop
from shop.shopDao import TinyShopDao
from shop.shopRepo import ShopRepo
from unit.testhelper import WebtomatorTestCase, ProductsUrlsRepoMock


class ShopRepoTest(WebtomatorTestCase):
    testDBPath = TEMP_SHOPS_TINYDB_TEST_PATH
    tempProductsUrlsRepoPath = PRODUCTS_URLS_TEST_DIR / "ProductsUrls_deleteMe.txt"

    def setUp(self) -> None:
        # Creates new DB at given path if not exists.
        # Deletes all records in all tables if DB exists.
        dbRef = tdb.TinyDB(str(self.testDBPath))
        dbRef.purge_tables()
        dbRef.close()

    def tearDown(self) -> None:
        if self.tempProductsUrlsRepoPath.is_file():
            self.tempProductsUrlsRepoPath.unlink()

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = ShopRepo

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getAll')
        self.assertHasAttribute(sut, 'setAll')
        self.assertHasAttribute(sut, 'update')

    def test_init_shouldSetDefaultValues(self):
        # When
        daoMock = Mock()
        daoMock.myValue = "DAO Mock checkValue"
        sut = ShopRepo(dao=daoMock)

        # Then
        self.assertEqual("DAO Mock checkValue", sut._dao.myValue)

    def test_getAll(self):
        # Given
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        # Create 2 shops in TinyDB for testing.
        # Note that we use client code to create them, which is more of an integration test...
        fixture = ShopFixture()
        fixture.create2Shops()
        expectedShops = fixture.shops
        ShopRepo(dao=testTinyShopDao).setAll(shops=expectedShops)

        sut = ShopRepo(dao=testTinyShopDao)

        # When
        loadedShops = sut.getAll()

        # Then
        # Expect that loaded shops match the expected
        self.assertEqual(expectedShops, loadedShops)

    def test_setAll(self):
        # Given
        # Insert a document into a fresh 'Shops' table. This data is expected to be
        # completely overridden by the test.
        existingData = dict(OneTestOne="Test data val 1", TwoTestTwo="Test data val 2")

        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            shopTable.insert(existingData)

        # These data are expected:
        fixture = ShopFixture()
        fixture.create2Shops()
        expectedShops = fixture.shops

        # Setup repo
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        sut = ShopRepo(dao=testTinyShopDao)

        # When
        sut.setAll(shops=expectedShops)

        # Then
        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            recordList: list = shopTable.all()

        # Expect that previous data do not exist anymore
        self.assertLessEqual(0, len(recordList))
        self.assertIsNone(recordList[0].get("OneTestOne"))
        self.assertIsNone(recordList[0].get("TwoTestTwo"))

        # Note that we use client code to load the shops again, which is
        # more of an integration test...
        loadedShops = sut.getAll()
        # Expect that loaded shops match the expected ones
        self.assertEqual(expectedShops, loadedShops)

    def test_update(self):
        # Given
        # Create 2 shops in TinyDB for testing.
        fixture = ShopFixture()
        fixture.create2Shops()
        expectedShop = fixture.shops[0]
        assert expectedShop.uid is not None and expectedShop.uid != ""

        # Write a shop which we can try to update by UID.
        existingData = dict(uid=expectedShop.uid, name="I don't know this shop's name")

        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            shopTable.insert(existingData)

        # Setup repo
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        sut = ShopRepo(dao=testTinyShopDao)

        # When
        sut.update(shop=expectedShop)

        # Then
        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            recordList: list = shopTable.all()

        self.assertEqual(1, len(recordList))
        # Expect that data with previous uid still exist
        self.assertEqual(expectedShop.uid, recordList[0].get("uid"))
        # Expect that shop's name has been updated
        self.assertNotEqual("I don't know this shop's name", recordList[0].get("name"))

        # Note that we use client code to load the shop again, which is
        # more of an integration test...
        updatedShops = sut.getAll()
        self.assertIsInstance(updatedShops, list)
        self.assertEqual(1, len(recordList))
        # Expect that updated shop matches the expected one
        self.assertEqual(expectedShop, updatedShops[0])

    def test_findByUID(self):
        # Given
        # Create test data to search for.
        uidToFind = "b0e2e467-6fd5-4a06-bb1e-9ad60223cafa"
        shopData1 = dict(uid="ca0f5926-7d55-4973-a8e1-d3e2cc89fca6",
                         name="The name of the first test shop")
        shopData2 = dict(uid=uidToFind,
                         name="The name of the second test shop")
        expectedShop = Shop(**shopData2)

        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            shopTable.insert(shopData1)
            shopTable.insert(shopData2)

        # Setup repo
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        sut = ShopRepo(dao=testTinyShopDao)

        # When
        foundShop = sut.findByUID(uidToFind)

        # Then
        self.assertIsInstance(foundShop, Shop)
        self.assertEqual(foundShop.uid, uidToFind)
        self.assertEqual(expectedShop, foundShop)

    def test_findByName(self):
        # Given
        # Create test data to search for. We use two shops with the same name here.
        shopData1 = dict(uid="ca0f5926-7d55-4973-a8e1-d3e2cc89fca6",
                         name="Shop with same name")
        shopData2 = dict(uid="e68782fd-19af-428e-881f-99d7af9b83b0",
                         name="This shop should not be found")
        shopData3 = dict(uid="b0e2e467-6fd5-4a06-bb1e-9ad60223cafa",
                         name="Shop with same name")
        expectedShops = [Shop(**shopData1), Shop(**shopData3)]

        with tdb.TinyDB(self.testDBPath) as db:
            shopTable: tdb.database.Table = db.table(TinyShopDao._TABLE_NAME)
            shopTable.insert(shopData1)
            shopTable.insert(shopData2)
            shopTable.insert(shopData3)

        # Setup repo
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        sut = ShopRepo(dao=testTinyShopDao)

        # When
        foundShops = sut.findByName("Shop with same name")

        # Then
        self.assertIsInstance(foundShops, list)
        self.assertEqual(2, len(foundShops))
        self.assertEqual(expectedShops, foundShops)

    def test_updateFromProductsUrls(self):
        # Given
        # Copy fixture to new arbitrary file as we will modify its contents within this test.
        with open(str(PRODUCTS_URLS_9_VALID_TEST_PATH), "r", encoding="utf-8") as source:
            content = source.read()
        with open(str(self.tempProductsUrlsRepoPath), "w+", encoding="utf-8") as target:
            target.write(content)

        # Note that the table gets deleted by the unit test's setup() method - so we
        # start with a fresh empty table.
        testTinyShopDao = TinyShopDao(path=self.testDBPath)
        sut = ShopRepo(dao=testTinyShopDao)

        productsUrlsRepo = ProductsUrlsRepoMock(productsUrlsRepoPath=self.tempProductsUrlsRepoPath)
        expectedProducts = productsUrlsRepo.getAll()
        expectedProductUrls = [p.url for p in expectedProducts]

        # 1. Test initial update -----------------------------------------------------------
        # When
        # This is expected to fill the table with all the fixture data of ProductsUrls repo.
        sut.updateFromProductsUrls(productsUrlsRepo=productsUrlsRepo)

        # Then
        shops = sut.getAll()
        self.assertIsInstance(shops, list)
        self.assertEqual(3, len(shops))

        # Expect that all shops have been inserted
        shopsUrls = [s.url for s in shops]
        self.assertIn("https://www.solebox.com", shopsUrls)
        self.assertIn("http://real.fantastic.de", shopsUrls)
        self.assertIn("https://www.dbyte.org", shopsUrls)

        # Expect that all products have been inserted
        soleboxShop = list(filter(lambda s: s.url == "https://www.solebox.com", shops))[0]
        self.assertIsInstance(soleboxShop.products, list)
        self.assertEqual(1, len(soleboxShop.products))
        for product in soleboxShop.products:
            self.assertIn(product.url, expectedProductUrls)

        realFantasticShop = list(filter(lambda s: s.url == "http://real.fantastic.de", shops))[0]
        self.assertIsInstance(realFantasticShop.products, list)
        self.assertEqual(2, len(realFantasticShop.products))
        for product in realFantasticShop.products:
            self.assertIn(product.url, expectedProductUrls)

        dbyteShop = list(filter(lambda s: s.url == "https://www.dbyte.org", shops))[0]
        self.assertIsInstance(dbyteShop.products, list)
        self.assertEqual(6, len(dbyteShop.products))
        for product in dbyteShop.products:
            self.assertIn(product.url, expectedProductUrls)

        # 2. Test delete product/shop -----------------------------------------------------
        # Given
        # Remove all http://real.fantastic.de/... URLs from ProductsUrls repo.
        with open(str(self.tempProductsUrlsRepoPath), "r+", encoding="utf-8") as target:
            lines = target.readlines()
            for line in reversed(lines):
                if line.startswith("http://real.fantastic.de/shop/great-realdumbtrump.htm"):
                    lines.remove(line)
                if line.startswith("http://real.fantastic.de/shop/buy-new-holo?prodid=682357ac"):
                    lines.remove(line)
            # Overwrite file with the updated data
            target.seek(0)
            target.writelines(lines)

        # When
        # This is expected to remove shop http://real.fantastic.de entirely from database,
        # because it's products do not exist anymore in ProductsUrls repo.
        sut.updateFromProductsUrls(productsUrlsRepo=productsUrlsRepo)

        # Then
        shops = sut.getAll()
        self.assertIsInstance(shops, list)
        self.assertEqual(2, len(shops))
        # Expect that shop http://real.fantastic.de has been entirely removed from database
        realFantasticShop = list(filter(lambda s: s.url == "http://real.fantastic.de", shops))
        self.assertIsInstance(realFantasticShop, list)
        self.assertEqual(0, len(realFantasticShop))

        # 3. Test add product to existing shop ----------------------------------------------
        # Given
        with open(str(self.tempProductsUrlsRepoPath), "r+", encoding="utf-8") as target:
            lines = target.readlines()
            lines.append("\nhttps://www.solebox.com/some-new-product\n")
            # Overwrite file with the updated data
            target.seek(0)
            target.writelines(lines)

        expectedProducts = productsUrlsRepo.getAll()
        expectedProductUrls = [p.url for p in expectedProducts]

        # When
        # This is expected to update shop https://www.solebox.com with the above added
        # product https://www.solebox.com/some-new-product
        sut.updateFromProductsUrls(productsUrlsRepo=productsUrlsRepo)

        # Then
        shops = sut.getAll()
        self.assertIsInstance(shops, list)
        self.assertEqual(2, len(shops))
        # Expect that product https://www.solebox.com/some-new-product has been added to
        # existing shop with URL https://www.solebox.com
        soleboxShop = list(filter(lambda s: s.url == "https://www.solebox.com", shops))[0]
        self.assertIsInstance(soleboxShop.products, list)
        self.assertEqual(2, len(soleboxShop.products))
        for product in soleboxShop.products:
            self.assertIn(product.url, expectedProductUrls)

        # 4. Test add shop to existing shops -------------------------------------------------
        # Given
        with open(str(self.tempProductsUrlsRepoPath), "r+", encoding="utf-8") as target:
            lines = target.readlines()
            lines.append("\nhttps://new-shop-1833663.com/new-product.htm\n")
            # Overwrite file with the updated data
            target.seek(0)
            target.writelines(lines)

        expectedProducts = productsUrlsRepo.getAll()
        expectedProductUrls = [p.url for p in expectedProducts]

        # When
        # This is expected to update the shop table (which already has shops in it) with
        # the above added product which has a base url which currently not exists
        # in the shops table. So a new shop with this product must be created in shopRepo.
        sut.updateFromProductsUrls(productsUrlsRepo=productsUrlsRepo)

        # Then
        shops = sut.getAll()
        self.assertIsInstance(shops, list)
        self.assertEqual(3, len(shops))
        # Expect that shop https://new-shop-1833663.com has been added to
        # existing database.
        newShop = list(filter(lambda s: s.url == "https://new-shop-1833663.com", shops))[0]
        self.assertIsInstance(newShop.products, list)
        self.assertEqual(1, len(newShop.products))
        for product in newShop.products:
            self.assertIn(product.url, expectedProductUrls)