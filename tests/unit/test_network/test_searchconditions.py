# unit.test_network.test_searchconditions.py
import unittest
from unittest.mock import Mock

import selenium.webdriver.common.by as selenium_by
from network.searchconditions import Strategy, SearchConditions, StrategyAdapter
from unit.testhelper import WebtomatorTestCase


class StrategyTest(WebtomatorTestCase):

    def test_ifWeKnowAllEnumCases(self):
        # Given
        sut = Strategy
        expectedCases = 5

        # When
        actual = sut.__len__()

        # Then
        self.assertEqual(
            expectedCases, actual,
            f"Enum {sut.__name__}: Found {actual} cases, expected"
            f" {expectedCases} cases. Check/extend all test cases for this Enum.")

    def test_ifEnumValuesAreCorrect(self):
        # Given
        sut = Strategy

        def errorMsg(a, b) -> str:
            return f"Enum case value is {a}, expected {b}"

        # When / Then
        actual = sut.IGNORE.value
        expected = "ignore"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.BY_ID.value
        expected = "id"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.BY_XPATH.value
        expected = "xPath"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.BY_CLASSNAME.value
        expected = "classname"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.BY_TEXT.value
        expected = "text"
        self.assertEqual(expected, actual, errorMsg(actual, expected))


class StrategyAdapterTest(WebtomatorTestCase):

    def test_toSelenium_shouldReturnSeleniumSearchStrategy(self):
        # Given / When / Then
        expectedSeleniumCase = None
        sut = StrategyAdapter(Strategy.IGNORE)
        self.assertEqual(expectedSeleniumCase, sut.toSelenium())

        expectedSeleniumCase = selenium_by.By.ID
        sut = StrategyAdapter(Strategy.BY_ID)
        self.assertEqual(expectedSeleniumCase, sut.toSelenium())

        expectedSeleniumCase = selenium_by.By.XPATH
        sut = StrategyAdapter(Strategy.BY_XPATH)
        self.assertEqual(expectedSeleniumCase, sut.toSelenium())

        expectedSeleniumCase = selenium_by.By.XPATH
        # this is correct as we are searching text content by selenium XPATH
        sut = StrategyAdapter(Strategy.BY_TEXT)
        self.assertEqual(expectedSeleniumCase, sut.toSelenium())


class SearchConditionsTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = SearchConditions

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'searchStrategy')
        self.assertHasAttribute(sut, 'identifier')

    def test_searchStrategy_shouldReturnValue(self):
        # Given
        expectedSearchStrategy = Mock(spec_set=Strategy)

        # When
        sut = SearchConditions(strategy=expectedSearchStrategy, identifier=Mock(spec=str))

        # Then
        self.assertEqual(expectedSearchStrategy, sut.searchStrategy)

    def test_identifier_shouldReturnValue(self):
        # Given
        expectedIdentifier = "A brandnew test identifier"

        # When
        sut = SearchConditions(strategy=Mock(spec=Strategy), identifier=expectedIdentifier)

        # Then
        self.assertEqual(expectedIdentifier, sut.identifier)


if __name__ == '__main__':
    unittest.main()