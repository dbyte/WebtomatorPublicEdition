# unit.test_shop.test_product.py
import uuid
from typing import List

import debug.logger as clog
import datetime as dtt
from unittest import mock

import pytz

from shop.product import Product, Size, StringProductUrlConverter, DictProductsUrlsConverter
from unit.testhelper import WebtomatorTestCase


class ProductTest(WebtomatorTestCase):

    def test_init_shouldSetDefaultProperties(self):
        # Given
        sut = Product()

        # Then
        self.assertNotEqual("", sut.uid)
        self.assertEqual(sut.uid, str(uuid.UUID(hex=sut.uid, version=4)))
        self.assertEqual("", sut.name)
        self.assertEqual(None, sut.basePrice)
        self.assertEqual(None, sut.currency)
        self.assertEqual("", sut.url)
        self.assertEqual(None, sut.urlThumb)
        self.assertEqual(None, sut.releaseDateStamp)
        self.assertEqual(0.0, sut.lastScanStamp)
        self.assertIsInstance(sut.sizes, list)
        self.assertEqual(0, len(sut.sizes))

    def test_lastScanStamp_shouldGetAndSet(self):
        # Given
        sut = Product()

        # When Setter
        sut.lastScanStamp = 123456789.987654321
        # Then Getter
        self.assertEqual(123456789.987654321, sut.lastScanStamp)

    def test_url_shouldGetAndSet(self):
        # Given
        sut = Product()

        # When Setter
        sut.url = "https://something-to-test/shop"
        # Then Getter
        self.assertEqual("https://something-to-test/shop", sut.url)

    def test_name_shouldGetAndSet(self):
        # Given
        sut = Product()

        # When Setter
        sut.name = "My smart product"
        # Then Getter
        self.assertEqual("My smart product", sut.name)

    def test_getPriceWithCurrency(self):
        # Given
        sut = Product(basePrice=1542.3, currency="€")
        # When
        result = sut.getPriceWithCurrency()
        # Then
        self.assertEqual("1542.30 €", result)

        # Given
        sut = Product(basePrice=20, currency="$")
        # When
        result = sut.getPriceWithCurrency()
        # Then
        self.assertEqual("20.00 $", result)

        # Given
        sut = Product(basePrice=20, currency=None)
        # When
        result = sut.getPriceWithCurrency()
        # Then
        self.assertEqual("20.00 [UNKNOWN CURRENCY]", result)

        # Given
        sut = Product(basePrice=None, currency="$")
        # When
        result = sut.getPriceWithCurrency()
        # Then
        self.assertEqual("unknown", result)

    def test_sizes_setterShouldSetCorrectValues(self):
        # Given
        sut = Product()
        sizeA = mock.Mock(spec=Size)
        sizeB = mock.Mock(spec=Size)
        sizeC = mock.Mock(spec=Size)
        sizeA.mockVal = 40
        sizeB.mockVal = 43.5
        sizeC.mockVal = 42.0
        expectedSizes = [sizeA, sizeB, sizeC]

        # When
        sut.sizes = expectedSizes

        # Then
        self.assertListEqual(expectedSizes, sut.sizes)

    def test_sizes_setterShouldRaiseOnInvalidType(self):
        # Given
        sut = Product()
        sizeA = mock.Mock(spec=Size)
        invalidType = mock.Mock()
        invalidList = [sizeA, invalidType]

        # When / Then
        with self.assertRaises(TypeError):
            sut.sizes = invalidList

    def test_addSize(self):
        # Given
        sut = Product()
        sizeA = Size(sizeEU="45.2")
        sizeB = Size(sizeEU="38.5")
        sizeC = Size(sizeEU="39")
        expectedSizes = [sizeA, sizeB, sizeC]

        # When
        sut.addSize(sizeA)
        sut.addSize(sizeB)
        sut.addSize(sizeC)

        # Then
        self.assertListEqual(expectedSizes, sut.sizes)

    def test_addSize_shouldRaiseTypeErrorOnInvalidType(self):
        # Given
        sut = Product()
        invalidType = mock.Mock(spec=dict)

        # When / Then
        with self.assertRaises(TypeError):
            sut.addSize(invalidType)

    def test_findSize(self):
        # Given
        sut = Product()
        sizeA = Size(sizeEU="41.25")
        sizeB = Size(sizeEU="38 2/3")
        sizeC = Size(sizeEU="39")
        sut.addSize(sizeA)
        sut.addSize(sizeB)
        sut.addSize(sizeC)

        # When given size not exists
        foundSize = sut.findSize(sizeStr="45")
        # Then
        self.assertIsNone(foundSize, f"Expected that size was not found and "
                                     f"returned value is None, but got '{foundSize}'")

        # When
        foundSize = sut.findSize(sizeStr=sizeA.sizeEU)
        # Then
        self.assertEqual(sizeA, foundSize)

        # When
        foundSize = sut.findSize(sizeStr=sizeB.sizeEU)
        # Then
        self.assertEqual(sizeB, foundSize)

        # When
        foundSize = sut.findSize(sizeStr=sizeC.sizeEU)
        # Then
        self.assertEqual(sizeC, foundSize)

    def test_getReleaseDate_shouldReturnDatetime(self):
        # Given
        sut = Product()

        givenTimezoneString = "US/Alaska"  # See also: pytz.all_timezones
        timezone = pytz.timezone(givenTimezoneString)
        givenDatetime = dtt.datetime(2035, 7, 15, 9, 00, 00)
        # Leave datetime itself untouched, just add the timezone-data:
        expectedLocalDatetime = timezone.localize(givenDatetime)

        sut.setReleaseDate(givenDatetime, timezone=givenTimezoneString)

        # When
        result = sut.getReleaseDate(forTimezone=givenTimezoneString, forType=dtt.datetime)

        # Then
        self.assertEqual(expectedLocalDatetime, result)

    def test_getReleaseDate_shouldReturnReadableString(self):
        # Given
        sut = Product()

        givenDatetime = dtt.datetime(2023, 11, 28, 13, 30, 12)
        givenTimezoneString = "Europe/Berlin"   # See also: pytz.all_timezones
        expectedString = "28.11.2023, 13:30:12"
        sut.setReleaseDate(givenDatetime, timezone=givenTimezoneString)

        # When
        result = sut.getReleaseDate(forTimezone=givenTimezoneString, forType=str)

        # Then
        self.assertEqual(expectedString, result)

    def test_getReleaseDate_shouldRaiseOnInvalidTimezoneString(self):
        # Given
        sut = Product()
        givenDatetime = dtt.datetime(2022, 12, 1, 8, 32, 59)
        sut.setReleaseDate(givenDatetime, timezone="Indian/Kerguelen")

        # When (forType str)
        with self.assertRaises(pytz.UnknownTimeZoneError):
            sut.getReleaseDate(forTimezone="Invalid/Something", forType=str)

        # When (forType datetime)
        with self.assertRaises(pytz.UnknownTimeZoneError):
            sut.getReleaseDate(forTimezone="EvenMoreInvalid/Stuff", forType=dtt.datetime)

    def test_getReleaseDate_shouldReturnNoneWhenReleaseStampIsNotSet(self):
        # Given
        sut = Product()
        sut.invalidateReleaseDate()

        # When
        result = sut.getReleaseDate(forTimezone="America/Indiana/Petersburg", forType=dtt.datetime)

        # Then
        self.assertEqual(None, result)

    def test_setReleaseDate_shouldSetCorrectDate(self):
        # Given
        sut = Product()

        berlinZone = pytz.timezone("Pacific/Fiji")  # See also: pytz.all_timezones
        givenDatetime = dtt.datetime(2020, 4, 18, 16, 00, 00)
        # Leave datetime itself untouched, just add the timezone-data:
        berlinDatetime = berlinZone.localize(givenDatetime)
        # Convert to UTC time:
        utcDatetime: dtt.datetime = berlinDatetime.astimezone(pytz.utc)
        # Convert to UNIX epoch float:
        expectedUtcTimestamp = utcDatetime.timestamp()  # 1587218400.0

        # When
        sut.setReleaseDate(givenDatetime, timezone="Pacific/Fiji")

        self.assertEqual(expectedUtcTimestamp, sut.releaseDateStamp)

    def test_setReleaseDate_shouldLogOnError(self):
        # Given
        sut = Product()
        givenDatetime = dtt.datetime(2020, 1, 30, 15, 40, 00)
        invalidTimezone = "very/invalid"

        loggerName = "shop.product"
        loggerUnderTest = clog.getLogger(loggerName)
        expectedLogLevel = "ERROR"
        expectedPartOfLogMessage = "Could not set product release date"

        # When
        with self.assertLogs(loggerUnderTest, level=expectedLogLevel) as tlog:
            sut.setReleaseDate(givenDatetime, timezone=invalidTimezone)

        # Then
        self.assertEqual(1, len(tlog.output))  # expect one single log message in array
        self.assertIn(f"{expectedLogLevel}:{loggerName}:{expectedPartOfLogMessage}", tlog.output[0])

    def test_invalidateReleaseDate(self):
        # Given
        sut = Product()
        givenDatetime = dtt.datetime(2028, 2, 27, 13, 5, 55)
        sut.setReleaseDate(givenDatetime, timezone="Africa/Bissau")  # See also: pytz.all_timezones

        # When
        sut.invalidateReleaseDate()

        # Then
        self.assertEqual(None, sut.releaseDateStamp)


class SizesTest(WebtomatorTestCase):

    def test_init_shouldSetDefaultProperties(self):
        # Given
        sut = Size()

        # Then
        self.assertNotEqual("", sut.uid)
        self.assertEqual(sut.uid, str(uuid.UUID(hex=sut.uid, version=4)))
        self.assertEqual(None, sut.sizeEU)
        self.assertEqual(None, sut.price)
        self.assertEqual(None, sut.url)
        self.assertEqual(None, sut.urlAddToCart)
        self.assertEqual(None, sut.isInStock)
        self.assertEqual("Unknown", sut.inStockReadable)

    def test_inStockReadable_shouldReturnCorrectString(self):
        # Given
        sut = Size()
        sut.isInStock = None

        # When
        result = sut.inStockReadable
        # Then
        self.assertEqual("Unknown", result)

        # Given
        sut.isInStock = False
        # When
        result = sut.inStockReadable
        # Then
        self.assertEqual("Out of stock", result)

        # Given
        sut.isInStock = True
        # When
        result = sut.inStockReadable
        # Then
        self.assertEqual("In stock", result)

    def test_inStockReadable_shouldRaiseOnTypeError(self):
        # Given
        sut = Size()
        sut.isInStock = "This is a string. But must be a bool!"
        # When
        with self.assertRaises(TypeError):
            result = sut.inStockReadable

            # Then
            self.assertEqual(None, result)


class StringProductUrlConverterTest(WebtomatorTestCase):

    def test_init_shouldSetAllowedTypes(self):
        # Given
        product = mock.Mock(spec_set=Product)

        # When
        sut = StringProductUrlConverter(product, str)

        # Then
        self.assertIs(sut._source, product)
        self.assertIs(sut._target, str)

    def test_getConverted_toProduct(self):
        # Given
        url = "http://www.url.com/products/superduperproduct-23468267.htm"
        sut = StringProductUrlConverter(url, Product)

        # When
        product = sut.getConverted()

        # Then
        self.assertEqual(url, product.url)

    def test_getConverted_toProduct_shouldReturnNoneOnEmptyUrlString(self):
        # Given
        emptyUrl = ""
        sut = StringProductUrlConverter(emptyUrl, Product)

        # When
        product = sut.getConverted()

        # Then
        self.assertIsNone(product)

    def test_getConverted_toProduct_shouldRaiseOnInvalidUrl(self):
        # Given
        invalidURL = "www.url.com/invalid-since-no-schema-given/superduperproduct-23468267.htm"
        sut = StringProductUrlConverter(invalidURL, Product)
        # When / Then
        with self.assertRaises(ValueError):
            sut.getConverted()

        # Given
        invalidURL = "invalid-since-no-url-at-all"
        sut = StringProductUrlConverter(invalidURL, Product)
        # When / Then
        with self.assertRaises(ValueError):
            sut.getConverted()

    def test_getConverted_toUrlString(self):
        # Given
        product = mock.Mock(spec=Product)
        product.url = mock.Mock(spec=str)
        product.url = "https://www.url.com/products/superduperproduct.php?x=284673"
        sut = StringProductUrlConverter(product, str)

        # When
        urlString = sut.getConverted()

        # Then
        self.assertEqual(product.url, urlString)

    def test_getConverted_toUrlString_shouldReturnNoneOnEmptyProductUrl(self):
        # Given
        product = mock.Mock(spec=Product)
        product.url = mock.Mock(spec=str)
        product.url = ""
        sut = StringProductUrlConverter(product, str)

        # When
        urlString = sut.getConverted()

        # Then
        self.assertIsNone(urlString)

    def test_getConverted_toUrlString_shouldReturnNoneOnNoneProductUrl(self):
        # Given
        product = mock.Mock(spec=Product)
        product.url = mock.Mock(spec=str)
        product.url = None
        sut = StringProductUrlConverter(product, str)

        # When
        urlString = sut.getConverted()

        # Then
        self.assertIsNone(urlString)


class DictProductsUrlsConverterTest(WebtomatorTestCase):

    def test_init_shouldSetAllowedTypes(self):
        # Given
        product01 = mock.Mock(spec_set=Product)
        product02 = mock.Mock(spec_set=Product)
        products = [product01, product02]

        # When
        sut = DictProductsUrlsConverter(products, dict)

        # Then
        self.assertIs(sut._source, products)
        self.assertIs(sut._target, dict)

    def test_defaultRecordsKey(self):
        # Given
        expectedDefaultValue = "data"

        # When
        currentDefaultValue = DictProductsUrlsConverter.URL_RECORDS_KEY

        # Then
        self.assertEqual(expectedDefaultValue, currentDefaultValue)

    def test_getConverted_toProducts(self):
        # Given
        dictRootKey = DictProductsUrlsConverter.URL_RECORDS_KEY
        urlList = ["http://www.url.com/products/superduperproduct-23468267.htm",
                   "",
                   "https://shops.everywhere.com/buy/shiny/new-prod-2947473",
                   ""
                   ]
        dataDict = {dictRootKey: urlList}

        sut = DictProductsUrlsConverter(dataDict, List[Product])

        # When
        products: List[Product] = sut.getConverted()

        # Then
        self.assertIsInstance(products, list)
        self.assertTrue(all(isinstance(elem, Product) for elem in products))
        self.assertEqual(2, len(products))
        self.assertEqual(urlList[0], products[0].url)
        self.assertEqual(urlList[2], products[1].url)

    def test_getConverted_shouldRaiseWhenNoMatchingDictKeyWasFound(self):
        # Given
        urlList = ["https://shops.everywhere.com/buy/shiny/new-prod-2947473"]
        dataDict = {"ThisDictKeyDoesNotMatch": urlList}

        sut = DictProductsUrlsConverter(dataDict, List[Product])

        # When / Then
        with self.assertRaises(KeyError):
            sut.getConverted()

    def test_getConverted_toDict(self):
        # Given
        dictRootKey = DictProductsUrlsConverter.URL_RECORDS_KEY
        product01 = mock.Mock(spec=Product)
        product02 = mock.Mock(spec=Product)
        product03 = mock.Mock(spec=Product)
        product01.url = "https://shops.everywhere.com/buy/shiny/new-prod-2947473"
        product02.url = ""
        product03.url = "http://www.url.com/products/superduperproduct-23468267.htm"
        products = [product01, product02, product03]

        sut = DictProductsUrlsConverter(products, dict)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        dataList = dataDict.get(dictRootKey)
        self.assertEqual(2, len(dataList))
        self.assertEqual(product01.url, dataList[0])
        self.assertEqual(product03.url, dataList[1])
