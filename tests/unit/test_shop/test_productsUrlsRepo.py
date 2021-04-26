# unit.test_shop.test_productsUrlsRepo.py
from typing import TYPE_CHECKING
from unittest.mock import Mock

from fixtures.shop import PRODUCTS_URLS_9_VALID_TEST_PATH, PRODUCTS_URLS_0_VALID_TEST_PATH
from shop.product import Product
from shop.productsUrlsDao import ProductsUrlsDao
from shop.productsUrlsRepo import ProductsUrlsRepo

from unit.testhelper import WebtomatorTestCase

if TYPE_CHECKING:
    from typing import List
    from shop.shop import Shop


class ProductsUrlsRepoTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = ProductsUrlsRepo

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getAll')

    def test_init_shouldSetDefaultValues(self):
        # When
        daoMock = Mock()
        daoMock.myValue = "DAO Mock checkValue"
        sut = ProductsUrlsRepo(dao=daoMock)

        # Then
        self.assertEqual("DAO Mock checkValue", sut._dao.myValue)

    def test_getAll(self):
        # Given
        testUrlsDao = ProductsUrlsDao(filepath=PRODUCTS_URLS_9_VALID_TEST_PATH)
        sut = ProductsUrlsRepo(dao=testUrlsDao)

        # When
        products = sut.getAll()

        # Then
        self.assertIsInstance(products, list)
        self.assertTrue(all(isinstance(i, Product) for i in products),
                        "Expected that all list elements are of type 'Product'")
        self.assertEqual(9, len(products))

    def test_createShops(self):
        # Given
        testUrlsDao = ProductsUrlsDao(filepath=PRODUCTS_URLS_9_VALID_TEST_PATH)
        sut = ProductsUrlsRepo(dao=testUrlsDao)

        # When
        shops: List[Shop] = sut.createShops()

        # Then
        self.assertIsInstance(shops, list)
        self.assertEqual(3, len(shops))
        shopsUrls = [s.url for s in shops]
        self.assertIn("https://www.solebox.com", shopsUrls)
        self.assertIn("https://www.dbyte.org", shopsUrls)
        self.assertIn("http://real.fantastic.de", shopsUrls)

    def test_createShops_shouldRaiseIfNoValidURLsFound(self):
        # Given
        emptyUrlsDao = ProductsUrlsDao(filepath=PRODUCTS_URLS_0_VALID_TEST_PATH)
        sut = ProductsUrlsRepo(dao=emptyUrlsDao)

        # When
        with self.assertRaises(LookupError):
            sut.createShops()
