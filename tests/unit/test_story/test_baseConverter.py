# unit.test_story.test_baseConverter.py

from unittest.mock import Mock

from story.actionBundle import ActionBundle
from story.baseConverter import BaseConverter
from unit.testhelper import WebtomatorTestCase


class BaseConverterTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Check presence of vital public properties/methods
        self.assertHasAttribute(BaseConverter, 'getConverted')

    def test__init_shouldSetSourceAndTargetPropertiesIfArgumentsAreValid(self):
        # Given
        source: ActionBundle = ActionBundle(name="A test name", actions=[])
        target: type = dict

        # When
        sut = BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))

        # Then
        self.assertIsInstance(sut._source, ActionBundle)
        self.assertEqual("A test name", sut._source.name)
        self.assertIsInstance(sut._target, type)

    def test_init_shouldRaiseIfOneOrBothArgumentsAreOfNoneType(self):
        # Given
        source = None
        target = {"that": "this"}

        # When / Then
        with self.assertRaises(ValueError):
            BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))

        # Given
        source = ActionBundle(name="What", actions=[])
        target = None

        # When / Then
        with self.assertRaises(ValueError):
            BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))

        # Given
        source = None
        target = None

        # When / Then
        with self.assertRaises(ValueError):
            BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))

    def test_init_shouldRaiseIfSourceIsNotInstanceOfOneOfAllowedTypes(self):
        # Given
        source: dict = {}  # is dict and not str and not int, so should raise
        target = int

        # When / Then
        with self.assertRaises(TypeError):
            BaseConverter(source=source, target=target, allowedTypes=(str, int))

    def test_init_shouldRaiseIfTargetIsNotOfTypeType(self):
        # Given
        source = Mock(spec_set=ActionBundle)
        target = dict()  # This is an instance, not a type - so should raise

        # When / Then
        with self.assertRaises(TypeError):
            BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))

    def test_init_shouldRaiseIfTargetIsTypeAndIsNotInAllowedTypes(self):
        # Given
        source: dict = {}
        target = str  # Is type str, not ActionBundle - so should raise

        # When / Then
        with self.assertRaises(TypeError):
            BaseConverter(source=source, target=target, allowedTypes=(ActionBundle, dict))
