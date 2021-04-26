# unit.test_network.test_proxy.py
import typing as tp
from unittest import mock

import debug.logger as clog
from network.proxy import StringProxyConverter, Proxy, StringlistProxiesConverter
from story.baseConverter import BaseConverter
from unit.testhelper import WebtomatorTestCase, LogHelper


class ProxyTest(WebtomatorTestCase):

    def test_init_shouldSetDefaultValues(self):
        # When
        sut = Proxy()

        # Then
        self.assertEqual(sut.scheme, "http")
        self.assertEqual(sut.endpoint, "")
        self.assertEqual(sut.port, 0)
        self.assertEqual(sut.username, "")
        self.assertEqual(sut.pw, "")

    def test_make_shouldSetCorrectProperties(self):
        # When
        sut = Proxy.make(scheme="https",
                         endpoint="this.is.a.test",
                         port=8273,
                         username="Special",
                         pw="/Very*Special_"
                         )

        # Then
        self.assertEqual(sut.scheme, "https")
        self.assertEqual(sut.endpoint, "this.is.a.test")
        self.assertEqual(sut.port, 8273)
        self.assertEqual(sut.username, "Special")
        self.assertEqual(sut.pw, "/Very*Special_")

    def test_buildForRequest(self):
        # 1. With authentication fields
        # Given
        sut = Proxy.make(scheme="http",
                         endpoint="build.this.com",
                         port=2738,
                         username="My_Username",
                         pw="My_Password"
                         )
        # When
        buildString = sut.buildForRequest()
        # Then
        self.assertEqual("http://My_Username:My_Password@build.this.com:2738/", buildString)

        # 2. Without authentication fields
        # Given
        sut = Proxy.make(endpoint="another.endpoint.com", port=9283)
        # When
        buildString = sut.buildForRequest()
        # Then
        self.assertEqual("http://another.endpoint.com:9283/", buildString)

    def test_buildForRequest_shouldRaiseIfProxyHasInvalidValues(self):
        # Given
        sut = Proxy.make(scheme="invalidScheme",
                         endpoint="have.a.niceday",
                         port=2983,
                         username="My_Username",
                         pw="My_Password"
                         )
        # When / Then
        with self.assertRaises(ValueError):
            sut.buildForRequest()

    def test_isValid_shouldReturnTrueIfAllIsValid(self):
        # Given
        sut = Proxy.make(endpoint="have.a.niceday",
                         port=2983,
                         username="My_Username",
                         pw="My_Password"
                         )
        # When
        result = sut.isValid()

        # Then
        self.assertTrue(result)

    def test_isValid_shouldReturnFalseIfProxyIsConsideredInvalid(self):
        failedTestMsg = "Expected Proxy validation to return False, but got True."

        # Given
        sut = Proxy.make(endpoint="",
                         port=2983,
                         username="MissingEndpoint!",
                         pw="My_Password"
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(endpoint="MissingUsernameWhilePassIsGiven",
                         port=2983,
                         username="",
                         pw="My_Password"
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(endpoint="MissingPassWhileUsernameIsGiven",
                         port=2983,
                         username="MyUserName",
                         pw=""
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(scheme="",
                         endpoint="MissingScheme",
                         port=2950
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(endpoint="Colon:InField",
                         port=34
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(endpoint="this.and.that.de",
                         port=4865,
                         username="MyUserName",
                         pw="CommentChar#InField"
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)

        # Given
        sut = Proxy.make(endpoint="this.and.that.de",
                         port=4865,
                         username="Whitespace  in field",
                         pw="MySpasswort"
                         )
        # When
        result = sut.isValid()
        # Then
        self.assertFalse(result, failedTestMsg)


class StringProxyConverterTest(WebtomatorTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        LogHelper.activate(level=clog.DEBUG)

    @classmethod
    def tearDownClass(cls) -> None:
        LogHelper.reset()
        super().tearDownClass()

    def test_isInstanceOfBaseConverter(self):
        sut = StringProxyConverter("", Proxy)
        self.assertIsInstance(sut, BaseConverter)

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = StringProxyConverter

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getConverted')

    # ----------------------------------------------------------------------
    # String to Proxy
    # ----------------------------------------------------------------------

    def test_getConverted_toProxy_shouldReturnValidAuthProxy(self):
        # Given
        proxyStr = "one.proxy.com:8080:myusername:mypassword-Germany_session-jazeoenx"
        sut = StringProxyConverter(proxyStr, Proxy)

        # When
        proxy = sut.getConverted()

        # Then
        self.assertEqual("one.proxy.com", proxy.endpoint)
        self.assertEqual(8080, proxy.port)
        self.assertEqual("myusername", proxy.username)
        self.assertEqual("mypassword-Germany_session-jazeoenx", proxy.pw)

    def test_getConverted_toProxy_shouldReturnValidSimpleProxy(self):
        # Given
        proxyStr = "197.236.15.203:9345"
        sut = StringProxyConverter(proxyStr, Proxy)

        # When
        proxy = sut.getConverted()

        # Then
        self.assertEqual("197.236.15.203", proxy.endpoint)
        self.assertEqual(9345, proxy.port)
        self.assertEqual("", proxy.username)
        self.assertEqual("", proxy.pw)

    def test_getConverted_toProxy_shouldCallValidProxyCheck(self):
        # We won't test for invalid proxy strings here because there is a dedicated function
        # for this check which gets unit tested itself. Just test if this func is called.

        # Given
        proxyStr = "some.endpoint.de:3487"
        sut = StringProxyConverter(proxyStr, Proxy)

        # When
        with mock.patch("network.proxy.StringProxyConverter.isValidProxyString") as check:
            sut.getConverted()

            # Then
            check.assert_called_once_with(proxyStr)

    def test_isValidProxy(self):
        # Given
        sut = StringProxyConverter

        # When
        expectedTrue = sut.isValidProxyString("sa:8081:kjf:ghf7")
        # Then
        self.assertEqual(True, expectedTrue)

        # When
        expectedTrue = sut.isValidProxyString("212.144.254.99:80:ghf7@23:479+#.//ds")
        # Then
        self.assertEqual(True, expectedTrue)

        # When
        expectedTrue = sut.isValidProxyString("valid.url.path:7812:name:pass#j#")
        # Then
        self.assertEqual(True, expectedTrue)

        # When
        expectedTrue = sut.isValidProxyString("proxyWithoutAuthentication:7700")
        # Then
        self.assertEqual(True, expectedTrue)

        # When
        expectedFalse = sut.isValidProxyString("#ThisIsACommentedOutProxy")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("#    ThisIs:A:CommentedOut:Proxy")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("\nsomething:which:starts:withNewLine")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("somethingwhich has:a::whitespace")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("somethingwhichEndsWithNewLine\n")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("somethingwhich:hasOnly:TwoColons")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("somethingwhich:has:more:than:three:Colons")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString(":somethingwhich:starts:withAColon")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("proxyWithEmptyAuth:8181::")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString(":8181")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString(":1893:user:pass")
        # Then
        self.assertEqual(False, expectedFalse)

        # When
        expectedFalse = sut.isValidProxyString("missingUserName:2973::pass")
        # Then
        self.assertEqual(False, expectedFalse)

    # ----------------------------------------------------------------------
    # Proxy to String
    # ----------------------------------------------------------------------

    def test_getConverted_toString_shouldReturnValidAuthProxy(self):
        # Given
        proxy = Proxy.make(endpoint="abc.bar.de",
                           port=8021,
                           username="Tester",
                           pw="TestPW")

        expectedString = "abc.bar.de:8021:Tester:TestPW"
        sut = StringProxyConverter(source=proxy, target=str)

        # When
        proxyStr = sut.getConverted()

        # Then
        self.assertEqual(expectedString, proxyStr)

    def test_getConverted_toString_shouldReturnValidSimpleProxy(self):
        # Given
        proxy = Proxy.make(endpoint="foo.bar.baz", port=9031)
        expectedString = "foo.bar.baz:9031"
        sut = StringProxyConverter(source=proxy, target=str)

        # When
        proxyStr = sut.getConverted()

        # Then
        self.assertEqual(expectedString, proxyStr)

    def test_getConverted_toString_shouldReturnNoneOnEmptyProxy(self):
        # Given
        proxy = Proxy()
        sut = StringProxyConverter(source=proxy, target=str)

        # When
        proxyStr = sut.getConverted()

        # Then
        self.assertEqual(None, proxyStr)

    def test_getConverted_toString_shouldCallValidProxyCheck(self):
        # We won't test for invalid proxy strings here because there is a dedicated function
        # for this check which gets unit tested itself. Just test if this func is called.

        # Given
        proxy = Proxy.make(endpoint="foo.bar.baz", port=9031)
        sut = StringProxyConverter(source=proxy, target=str)

        # When
        with mock.patch("network.proxy.StringProxyConverter.isValidProxyString") as check:
            sut.getConverted()

            # Then
            check.assert_called_once()


class StringlistProxiesConverterTest(WebtomatorTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        LogHelper.activate(level=clog.DEBUG)

    @classmethod
    def tearDownClass(cls) -> None:
        LogHelper.reset()
        super().tearDownClass()

    def test_isInstanceOfBaseConverter(self):
        sut = StringlistProxiesConverter(list(), tp.List[Proxy])
        self.assertIsInstance(sut, BaseConverter)

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = StringlistProxiesConverter

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'getConverted')

    # ----------------------------------------------------------------------
    # List of strings to Proxies
    # ----------------------------------------------------------------------

    def test_getConverted_toProxies_shouldReturnCorrectInstance(self):
        # Given
        proxyStrings = [
            "foo.bar.de:8080:TestUser:TestPassword",
            "another.one.de:2846",
            "234.178.188.6:9274"
        ]

        sut = StringlistProxiesConverter(source=proxyStrings, target=tp.List[Proxy])

        # When
        proxies = sut.getConverted()

        # Then
        self.assertIsInstance(proxies, list)
        self.assertTrue(all(isinstance(i, Proxy) for i in proxies))

    def test_getConverted_toProxies_shouldSetObjectArray(self):
        # Given
        proxyStrings = [
            "foo.bar.de:8080:TestUser:TestPassword",
            "another.one.de:2846",
            "234.178.188.6:9274"
        ]

        sut = StringlistProxiesConverter(source=proxyStrings, target=tp.List[Proxy])

        # When
        proxies = sut.getConverted()

        # Then
        self.assertEqual(3, len(proxies))

        idx = 0
        self.assertEqual("foo.bar.de", proxies[idx].endpoint)
        self.assertEqual(8080, proxies[idx].port)
        self.assertEqual("TestUser", proxies[0].username)
        self.assertEqual("TestPassword", proxies[idx].pw)
        idx = 1
        self.assertEqual("another.one.de", proxies[idx].endpoint)
        self.assertEqual(2846, proxies[idx].port)
        self.assertEqual("", proxies[idx].username)
        self.assertEqual("", proxies[idx].pw)
        idx = 2
        self.assertEqual("234.178.188.6", proxies[idx].endpoint)
        self.assertEqual(9274, proxies[idx].port)
        self.assertEqual("", proxies[idx].username)
        self.assertEqual("", proxies[idx].pw)

    def test_getConverted_toProxies_shouldReturnRepoWithZeroProxiesOnEmptyList(self):
        # Given
        emptyList = []
        sut = StringlistProxiesConverter(source=emptyList, target=tp.List[Proxy])

        # When
        proxies = sut.getConverted()

        # Then
        self.assertIsInstance(proxies, list)
        self.assertEqual(0, len(proxies))
        self.assertTrue(all(isinstance(i, Proxy) for i in proxies))

    def test_getConverted_toProxies_ShouldSkipInvalidProxies(self):
        # Given
        someInvalid = [
            "foo.bar.de:8080:TestUser:TestPassword",
            "this.is.invalid::x",
            "234.178.188.6:9274"
        ]
        sut = StringlistProxiesConverter(source=someInvalid, target=tp.List[Proxy])

        # When
        proxies = sut.getConverted()

        # Then
        self.assertEqual(2, len(proxies))

        idx = 0
        self.assertEqual("foo.bar.de", proxies[idx].endpoint)
        self.assertEqual(8080, proxies[idx].port)
        self.assertEqual("TestUser", proxies[0].username)
        self.assertEqual("TestPassword", proxies[idx].pw)
        idx = 1
        self.assertEqual("234.178.188.6", proxies[idx].endpoint)
        self.assertEqual(9274, proxies[idx].port)
        self.assertEqual("", proxies[idx].username)
        self.assertEqual("", proxies[idx].pw)

    # ----------------------------------------------------------------------
    #  Proxy list to string list
    # ----------------------------------------------------------------------

    def test_getConverted_toStringlist_shouldSetStringList(self):
        # Given
        proxy1 = Proxy.make(endpoint="abc.bar.de",
                            port=8021,
                            username="Tester",
                            pw="TestPW")
        proxy2 = Proxy.make(endpoint="123.234.217.1",
                            port=3526,
                            username="",
                            pw="")
        proxies = list((proxy1, proxy2))

        sut = StringlistProxiesConverter(source=proxies, target=tp.List[str])

        # When
        stringList = sut.getConverted()

        # Then
        self.assertIsInstance(stringList, list)
        self.assertEqual(2, len(stringList))
        idx = 0
        self.assertEqual("abc.bar.de:8021:Tester:TestPW", stringList[idx])
        idx = 1
        self.assertEqual("123.234.217.1:3526", stringList[idx])

    def test_getConverted_toStringlist_shouldReturnEmptyListOnEmptyProxyObjectList(self):
        # Given
        emptyList = list()
        self.assertEqual(0, len(emptyList))

        sut = StringlistProxiesConverter(source=emptyList, target=tp.List[Proxy])

        # When
        stringList = sut.getConverted()

        # Then
        self.assertEqual(0, len(stringList))
        self.assertIsInstance(stringList, list)

    def test_getConverted_toStringlist_ShouldSkipInvalidProxies(self):
        # Given
        proxy1 = Proxy.make(endpoint="InvalidProxyMissingUsername",
                            port=2333,
                            username="",
                            pw="MyPass")
        proxy2 = Proxy.make(endpoint="186.230.153.100",
                            port=3526,
                            username="Some_User",
                            pw="Some+-Pass")
        proxies = list((proxy1, proxy2))

        sut = StringlistProxiesConverter(source=proxies, target=tp.List[str])

        # When
        stringList = sut.getConverted()

        # Then
        self.assertEqual(1, len(stringList))
        self.assertEqual("186.230.153.100:3526:Some_User:Some+-Pass", stringList[0])
