# unit.test_shop.test_productsUrlsDao.py
import urllib.parse

from fixtures.shop import PRODUCTS_URLS_TEST_DIR, PRODUCTS_URLS_9_VALID_TEST_PATH
from shop.product import Product
from shop.productsUrlsDao import ProductsUrlsDao
from unit.testhelper import WebtomatorTestCase


class ProductsUrlsDaoTest(WebtomatorTestCase):
    testDir = PRODUCTS_URLS_TEST_DIR
    testFilePath = PRODUCTS_URLS_9_VALID_TEST_PATH

    def test_init_shouldSetDefaultPathIfNoPathIsGiven(self):
        # When
        sut = ProductsUrlsDao()

        # Then
        self.assertEqual(ProductsUrlsDao._DEFAULT_PATH, sut.connection.path)

    def test_init_shouldSetGivenPath(self):
        # When
        sut = ProductsUrlsDao(self.testDir)

        # Then
        self.assertEqual(self.testDir, sut.connection.path)

    def test_loadAll(self):
        # Given
        pathToFixture = PRODUCTS_URLS_9_VALID_TEST_PATH

        # When
        with ProductsUrlsDao(pathToFixture) as sut:
            productList = sut.loadAll()

        # Then
        # Expect that result is of type list
        self.assertIsInstance(productList, list)
        # Expect that all elements of list are of type Product
        self.assertTrue(all(isinstance(i, Product) for i in productList))
        # Expect we got 9 valid urls and any lines starting with '#' have been filtered.
        self.assertEqual(9, len(productList))
        # Expect we got 2 products whose URLs contain "real.fantastic.de"
        self.assertEqual(2, len(list(filter(lambda p: "real.fantastic.de" in p.url, productList))))
        # Expect every product URL can be split into scheme and netloc by urlsplit
        for product in productList:
            try:
                parsedURL = urllib.parse.urlsplit(product.url)
                self.assertNotEqual("", parsedURL.netloc)
                self.assertNotEqual("", parsedURL.scheme)

            except Exception as e:
                self.fail(f"Expected URL being able to be parsed, but failed with: {e}")

    def test_saveAll(self):
        # Given
        path = PRODUCTS_URLS_TEST_DIR / f"{__class__.__name__}.test_saveAll.txt"
        expectedURLs = ["https://www.dbyte.org/shop/one/product01.html",
                        "https://www.dbyte.org/shop/one/another-product02.html"]

        product01 = Product()
        product02 = Product()
        product01.url = expectedURLs[0]
        product02.url = expectedURLs[1]
        products = [product01, product02]

        # When
        with ProductsUrlsDao(path) as sut:
            sut.saveAll(data=products)

        # Then
        with open(str(path), "r", encoding="utf-8") as file:
            lines = [line.replace("\n", "") for line in file.readlines()]
            self.assertListEqual(expectedURLs, lines)

        path.unlink()

    def test_saveAll_shouldRaiseIfGivenDataIsNotAListOfProducts(self):
        # Given
        path = PRODUCTS_URLS_TEST_DIR / "should-not-have-been-saved.txt"
        dataWithInvalidType = ["A string element", "This should be an invalid data list"]

        # When
        with self.assertRaises(TypeError):
            with ProductsUrlsDao(path) as sut:
                # noinspection PyTypeChecker
                sut.saveAll(data=dataWithInvalidType)

        path.unlink()

    def test_deleteAll(self):
        # Given
        path = PRODUCTS_URLS_TEST_DIR / "test_deleteAll.txt"
        data = "http://www.google.de/shop/delete-me-01.htm\n" \
               "https://www.dbyte.org/delete-me-02.htm"
        # First, create a file with some textual data
        with open(str(path), "w+", encoding="utf-8") as file:
            file.write(data)
        with open(str(path), "r", encoding="utf-8") as file:
            testData = file.read()
        # Check precondition for the main test, we need some data in here.
        self.assertEqual(data, testData)

        # When
        with ProductsUrlsDao(path) as sut:
            sut.deleteAll()

        # Then
        # Expect that content of file has been deleted.
        with open(str(path), "r", encoding="utf-8") as fileAfterDeletedContent:
            dataAfterDeletion = fileAfterDeletedContent.read()
        self.assertEqual("", dataAfterDeletion)

        path.unlink()