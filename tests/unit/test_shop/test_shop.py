# unit.test_shop.test_shop.py
import uuid
from unittest import mock

from shop.product import Product
from shop.shop import Shop
from unit.testhelper import WebtomatorTestCase


class ShopTest(WebtomatorTestCase):

    def test_init_shouldSetDefaultProperties(self):
        # Given
        sut = Shop()

        # Then
        self.assertNotEqual("", sut.uid)
        self.assertEqual(sut.uid, str(uuid.UUID(hex=sut.uid, version=4)))
        self.assertEqual("", sut.name)
        self.assertEqual("", sut.url)
        self.assertEqual(0.0, sut.lastScanStamp)
        self.assertEqual(0, len(sut.products))

    def test_url_shouldGetAndSet(self):
        # Given
        sut = Shop()

        # When Setter
        sut.url = "https://something-to-test/shop"
        # Then Getter
        self.assertEqual("https://something-to-test/shop", sut.url)

    def test_name_shouldGetAndSet(self):
        # Given
        sut = Shop()

        # When Setter
        sut.name = "My huge shop"
        # Then Getter
        self.assertEqual("My huge shop", sut.name)

    def test_lastScanStamp_shouldGetAndSet(self):
        # Given
        sut = Shop()

        # When Setter
        sut.lastScanStamp = 123456789.987654321
        # Then Getter
        self.assertEqual(123456789.987654321, sut.lastScanStamp)

    def test_products_setterShouldSetCorrectValues(self):
        # Given
        sut = Shop()
        prodA = mock.Mock(spec=Product)
        prodB = mock.Mock(spec=Product)
        prodC = mock.Mock(spec=Product)

        prodA.mockVal = "Some product mock A"
        prodB.mockVal = "Some product mock B"
        prodC.mockVal = "Some product mock C"
        expectedProducts = [prodA, prodB, prodC]

        # When
        sut.products = expectedProducts

        # Then
        self.assertListEqual(expectedProducts, sut.products)

    def test_products_setterShouldRaiseOnInvalidType(self):
        # Given
        sut = Shop()
        prodA = mock.Mock(spec=Product)
        invalidType = mock.Mock()
        invalidList = [prodA, invalidType]

        # When / Then
        with self.assertRaises(TypeError):
            sut.products = invalidList

    def test_addProduct(self):
        # Given
        sut = Shop()
        prodA = mock.Mock(spec=Product)
        prodB = mock.Mock(spec=Product)
        prodC = mock.Mock(spec=Product)
        prodA.url = "Some product mock A"
        prodB.url = "Some product mock B"
        prodC.url = "Some product mock C"
        expectedProducts = [prodA, prodB, prodC]

        # When
        sut.addProduct(prodA)
        sut.addProduct(prodB)
        sut.addProduct(prodC)

        # Then
        self.assertListEqual(expectedProducts, sut.products)

    def test_addProduct_shouldNotAddProductWithSameUrlAgain(self):
        # Given
        sut = Shop()
        prodA = mock.Mock(spec=Product)
        prodB = mock.Mock(spec=Product)
        prodC = mock.Mock(spec=Product)
        prodA.url = "http://url-value-A.com/"
        prodB.url = "https://some-other-url.io"
        prodC.url = "http://url-value-A.com/"
        expectedProducts = [prodA, prodB]  # NOT prodC !

        # When
        sut.addProduct(prodA)
        sut.addProduct(prodB)
        sut.addProduct(prodC)

        # Then
        self.assertEqual(2, len(sut.products))
        self.assertListEqual(expectedProducts, sut.products)

    def test_addProduct_shouldRaiseTypeErrorOnInvalidType(self):
        # Given
        sut = Shop()
        prodA = mock.Mock()
        prodA.mockVal = "Some product mock"

        # When / Then
        with self.assertRaises(TypeError):
            sut.addProduct(prodA)

    def test_removeProduct(self):
        # Given
        sut = Shop()
        prodA = mock.Mock(spec=Product)
        prodB = mock.Mock(spec=Product)
        prodC = mock.Mock(spec=Product)
        prodA.mockVal = "Some product mock A"
        prodB.mockVal = "Some product mock B"
        prodC.mockVal = "Some product mock C"
        expectedProducts = [prodA]
        sut.products = [prodA, prodB, prodC]

        # When
        sut.removeProduct(prodB)
        sut.removeProduct(prodC)

        # Then
        self.assertListEqual(expectedProducts, sut.products)

    def test_removeProduct_shouldRaiseTypeErrorOnInvalidType(self):
        # Given
        sut = Shop()
        prodA = mock.Mock()
        prodA.mockVal = "Some product mock"

        # When / Then
        with self.assertRaises(TypeError):
            sut.removeProduct(prodA)

    def test_getNetloc(self):
        # Given
        sut = Shop()
        sut.url = "https://www.43einhalb.com/new-balance-m997sob-made-in-usa"
        expectedNetloc = "www.43einhalb.com"

        # When
        result = sut.getNetloc()
        # Then
        self.assertEqual(expectedNetloc, result)

        # Given
        sut.url = "https://bubblegum.com/en/new-996-vhb-wl996vhb.html"
        expectedNetloc = "bubblegum.com"
        # When
        result = sut.getNetloc()
        # Then
        self.assertEqual(expectedNetloc, result)

        # Given
        sut.url = "http://www.somewhere.de/bubu/ghj45-3879475?req=nothing"
        expectedNetloc = "www.somewhere.de"
        # When
        result = sut.getNetloc()
        # Then
        self.assertEqual(expectedNetloc, result)

    def test_getNetloc_shouldRaiseWhenNotExtractable(self):
        # Given
        sut = Shop()
        sut.url = "www.scary-tests.com/url-has-missing-schema.html"

        # When
        with self.assertRaises(ValueError):
            sut.getNetloc()

    def test_assignProducts(self):
        # Given
        sut = Shop()
        shopURL = "http://this-is-the-netloc-part.com"
        sut.url = shopURL

        # Any product with the same URL netloc part as the shop's URL netloc part
        # is expected to be added to the shop's products list.
        productMock_01 = mock.Mock(spec=Product)
        productMock_01.url = "http://this-is-the-netloc-part.com/en/some_product_link_284734.htm"
        productMock_02 = mock.Mock(spec=Product)
        productMock_02.url = "http://this-is-the-netloc-part.com/en/some_other_product_9274692"
        productMock_03 = mock.Mock(spec=Product)
        productMock_03.url = "http://another-shop.org/some_other_product_9274692.php"

        products = list()
        products.extend([productMock_01, productMock_02, productMock_03])

        # When
        addedProducts = sut.assignProducts(products)

        # Then
        # productMock_03 should NOT be in the shop's products list.
        self.assertEqual(2, len(sut.products))
        self.assertEqual(productMock_01.url, sut.products[0].url)
        self.assertEqual(productMock_02.url, sut.products[1].url)
        self.assertIsInstance(addedProducts, list)
        self.assertEqual(2, len(addedProducts))

    def test_assignProducts_shouldNotAddIfNoProducts(self):
        # Given
        sut = Shop()
        shopURL = "http://this-again-is-a-netloc-part.com"
        sut.url = shopURL

        products = None
        # When
        # noinspection PyTypeChecker
        sut.assignProducts(products)
        # Then
        self.assertEqual(0, len(sut.products))

        # Given
        products = list()
        # When
        addedProducts = sut.assignProducts(products)
        # Then
        self.assertEqual(0, len(sut.products))
        self.assertIsInstance(addedProducts, list)
        self.assertEqual(0, len(addedProducts))