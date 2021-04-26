# unit.test_story.test_actionBundleConverter.py
from unittest.mock import Mock

from network.searchconditions import Strategy, SearchConditions
from story.action import LoadPageAction, WaitUntilVisibleAction, SubmitAction, SendKeysAction
from story.actionBundle import ActionBundle
from story.actionBundleConverter import DictActionBundleConverter
from unit.testhelper import WebtomatorTestCase


class DictActionBundleConverterTest(WebtomatorTestCase):

    def setUp(self) -> None:
        self.sut = DictActionBundleConverter
        self.TABLE_NAME = "ActionBundles"

    def tearDown(self) -> None:
        del self.sut, self.TABLE_NAME

    def test_ifVitalAttributesArePresent(self):
        # Check presence of vital public properties/methods
        self.assertHasAttribute(self.sut, 'getConverted')

    def test_getConverted_toActionBundle_shouldReturnEmptyActionBundleIfDictIsEmpty(self):
        # Given
        dataDict = {}
        converter = self.sut(source=dataDict, target=ActionBundle, table=self.TABLE_NAME)

        # When
        actualActionBundle = converter.getConverted()

        # Then
        self.assertIsInstance(actualActionBundle, ActionBundle)
        self.assertEqual(0, len(actualActionBundle.actions))
        self.assertEqual("New", actualActionBundle.name)

    def test_getConverted_toActionBundle_shouldRaiseIfDictIsNone(self):
        # Given
        dataDict = None

        # When / Then
        with self.assertRaises(ValueError):
            self.sut(source=dataDict, target=ActionBundle, table=self.TABLE_NAME)

    def test_getConverted_toActionBundle_shouldReturnEmptyActionBundleOnKeyError(self):
        # Given
        dataDict = {
            "invalidKey_test1": 1.0,
            "invalidKey_test2": "Some test bundle name",
            "invalidKey_test3": [
                {
                    "invalidKey_test4": 6,
                }
            ]
        }
        converter = self.sut(source=dataDict, target=ActionBundle, table=self.TABLE_NAME)

        # When
        actualActionBundle = converter.getConverted()

        # Then
        self.assertIsInstance(actualActionBundle, ActionBundle)
        self.assertEqual(0, len(actualActionBundle.actions))
        self.assertEqual("New", actualActionBundle.name)

    def test_getConverted_toActionBundle_shouldReturnValidActionBundle(self):
        # Given
        dataDict = {
            "version": 1.0,
            "name": "Test Action Bundle",
            "actions": [
                {
                    "command": 2,
                    "searchStrategy": "",
                    "searchIdentifier": "",
                    "textToSend": "https://google.de",
                    "maxWait": 0.0
                },
                {
                    "command": 6,
                    "searchStrategy": "text",
                    "searchIdentifier": "This is a test identifier",
                    "textToSend": "",
                    "maxWait": 5.0
                }
            ]
        }
        converter = self.sut(source=dataDict, target=ActionBundle, table=self.TABLE_NAME)

        # When
        actualActionBundle = converter.getConverted()

        # Then
        # A valid ActionBundle object
        self.assertIsInstance(actualActionBundle, ActionBundle)
        # Expect 2 Actions within Actionbundle
        self.assertEqual(2, len(actualActionBundle.actions))

        # Expect that first Action is a LoadPageAction object
        self.assertIsInstance(actualActionBundle.actions[0], LoadPageAction)
        # Expect correct "name" property of the ActionBundle
        self.assertEqual("Test Action Bundle", actualActionBundle.name)
        # Expect correct "textToSend" property value of the LoadPageAction
        self.assertEqual("https://google.de", actualActionBundle.actions[0].textToSend)

        # Expect 2nd Action to be an instance of class WaitUntilVisibleAction
        self.assertIsInstance(actualActionBundle.actions[1], WaitUntilVisibleAction)
        # Expect Strategy of 2nd Action to be Strategy.BY_TEXT
        self.assertEqual(Strategy.BY_TEXT,
                         actualActionBundle.actions[1].searchConditions.searchStrategy)
        # Expect identifier string of 2nd Action to match with identifier in dict
        self.assertEqual("This is a test identifier",
                         actualActionBundle.actions[1].searchConditions.identifier)
        # Expect maxWait in 2nd Action to be 5.0
        self.assertEqual(5.0,
                         actualActionBundle.actions[1].maxWait)

    def test_getConverted_toDict_shouldReturnValidDictIfActionBundleHasNoActions(self):
        # Given
        actionBundle = ActionBundle(name="Test title", actions=[])
        converter = self.sut(source=actionBundle, target=dict, table=self.TABLE_NAME)

        # When
        dataDict = converter.getConverted()

        # Then
        # Expect it is a dict object
        self.assertIsInstance(dataDict, dict)
        # Expect we have a dict with 3 items
        self.assertEqual(3, len(dataDict))

        self.assertIn("name", dataDict)
        self.assertEqual("Test title", dataDict["name"])
        self.assertIn("actions", dataDict)
        self.assertEqual(0, len(dataDict["actions"]))

    def test_getConverted_toDict_shouldRaiseIfActionBundleIsNone(self):
        # Given
        actionBundle = None

        # When / Then
        with self.assertRaises(ValueError):
            self.sut(source=actionBundle, target=dict, table=self.TABLE_NAME)

    def test_getConverted_toDict_shouldReturnValidDict(self):
        # Given
        sc1 = Mock(spec_set=SearchConditions)
        sc2 = Mock(spec_set=SearchConditions)
        sc1.searchStrategy.value = "strategy1"
        sc1.identifier = "id1"
        sc2.searchStrategy.value = "strategy2"
        sc2.identifier = "id2"
        action1 = SubmitAction(searchConditions=sc1)
        action2 = SendKeysAction(searchConditions=sc2, text="This is a test text to send")
        actionBundle = ActionBundle(name="A test title", actions=[action1, action2])
        converter = self.sut(source=actionBundle, target=dict, table=self.TABLE_NAME)

        # When
        dataDict = converter.getConverted()

        # Then
        # Expect it is a dict object
        self.assertIsInstance(dataDict, dict)
        # Expect the dict has 3 items
        self.assertEqual(3, len(dataDict))
        # Expect it has a "name" key on its top level
        self.assertIn("name", dataDict)
        # Expect it has an "version" key on its top level
        self.assertIn("version", dataDict)
        # Expect it has an "actions" key on its top level
        self.assertIn("actions", dataDict)
        # Expect the dict has a list of 2 actions
        self.assertEqual(2, len(dataDict["actions"]))

        # Expect the 1st item of array "actions" has a key "command"
        self.assertIn("command", dataDict["actions"][0])
        # Expect the command value for key "command" matches 5 (which is ActionCmd.SUBMIT)
        self.assertEqual(5, dataDict["actions"][0]["command"])
        # Expect value of key "searchStrategy" and "searchIdentifier"
        # in the 1st item of array "actions" to match the formerly given values
        self.assertIn("searchStrategy", dataDict["actions"][0])
        self.assertEqual("strategy1", dataDict["actions"][0]["searchStrategy"])
        self.assertIn("searchIdentifier", dataDict["actions"][0])
        self.assertEqual("id1", dataDict["actions"][0]["searchIdentifier"])

        # Expect the 2nd item of array "actions" has a key "textToSend"
        self.assertIn("textToSend", dataDict["actions"][1])
        # Expect the value for key "textToSend" matches
        self.assertEqual("This is a test text to send", dataDict["actions"][1]["textToSend"])
        # Expect value of key "searchStrategy" and "searchIdentifier"
        # in the 2nd item of array "actions" to match the formerly given values
        self.assertIn("searchStrategy", dataDict["actions"][1])
        self.assertEqual("strategy2", dataDict["actions"][1]["searchStrategy"])
        self.assertIn("searchIdentifier", dataDict["actions"][1])
        self.assertEqual("id2", dataDict["actions"][1]["searchIdentifier"])
