# unit.test_story.test_actionConverter.py

from unittest.mock import Mock

from network.searchconditions import Strategy, SearchConditions
from story.action import LoadPageAction, ActionCmd, Action, SendKeysAction, ClickAction, \
    SubmitAction, WaitUntilVisibleAction, PauseAction, QuitBrowserAction
from story.actionConverter import DictActionConverter
from unit.testhelper import WebtomatorTestCase


class DictActionConverterTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Check presence of vital public properties/methods
        self.assertHasAttribute(DictActionConverter, 'getConverted')

    def test_init_shouldSetValidProperties(self):
        # Given
        source: dict = {"expectedTestKey": "expectedTestValue"}
        target = Action

        # When
        sut = DictActionConverter(source, target)

        # Then
        self.assertIsInstance(sut._source, dict)
        self.assertIs(sut._target, Action)

        self.assertDictEqual(source, sut._source)

    # ------------------------------------------------------------------------------------
    # Following tests expect dict as source and Action as target
    # ------------------------------------------------------------------------------------

    def test_dictToAction_shouldRaiseValueIfCommandIsUnknown(self):
        # Given
        source: dict = {
            "command": "This is an invalid test command",
            "searchStrategy": 0,
            "searchIdentifier": "",
            "textToSend": "",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When / Then
        with self.assertRaises(ValueError):
            sut.getConverted()

    def test_dictToAction_LoadPageAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.LOAD_PAGE.value,
            "searchStrategy": Strategy.IGNORE.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, LoadPageAction)
        self.assertEqual(ActionCmd.LOAD_PAGE, action.command)
        self.assertEqual("Test value of textToSend", action.textToSend)

    def test_dictToAction_SendKeysAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.SEND_KEYS.value,
            "searchStrategy": Strategy.BY_XPATH.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, SendKeysAction)
        self.assertEqual(ActionCmd.SEND_KEYS, action.command)
        self.assertEqual(Strategy.BY_XPATH, action.searchConditions.searchStrategy)
        self.assertEqual("Test value of searchIdentifier", action.searchConditions.identifier)
        self.assertEqual("Test value of textToSend", action.textToSend)

    def test_dictToAction_ClickAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.CLICK.value,
            "searchStrategy": Strategy.BY_ID.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, ClickAction)
        self.assertEqual(ActionCmd.CLICK, action.command)
        self.assertEqual(Strategy.BY_ID, action.searchConditions.searchStrategy)
        self.assertEqual("Test value of searchIdentifier", action.searchConditions.identifier)

    def test_dictToAction_SubmitAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.SUBMIT.value,
            "searchStrategy": Strategy.BY_TEXT.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, SubmitAction)
        self.assertEqual(ActionCmd.SUBMIT, action.command)
        self.assertEqual(Strategy.BY_TEXT, action.searchConditions.searchStrategy)
        self.assertEqual("Test value of searchIdentifier", action.searchConditions.identifier)

    def test_dictToAction_WaitUntilVisibleAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.WAIT_UNTIL_VISIBLE.value,
            "searchStrategy": Strategy.BY_XPATH.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 2.65
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, WaitUntilVisibleAction)
        self.assertEqual(ActionCmd.WAIT_UNTIL_VISIBLE, action.command)
        self.assertEqual(Strategy.BY_XPATH, action.searchConditions.searchStrategy)
        self.assertEqual("Test value of searchIdentifier", action.searchConditions.identifier)
        self.assertEqual(2.65, action.maxWait)

    def test_dictToAction_PauseAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.PAUSE.value,
            "searchStrategy": Strategy.BY_XPATH.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 10
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, PauseAction)
        self.assertEqual(ActionCmd.PAUSE, action.command)
        self.assertEqual(10, action.maxWait)

    def test_dictToAction_QuitBrowserAction(self):
        # Given
        source: dict = {
            "command": ActionCmd.QUIT_BROWSER.value,
            "searchStrategy": Strategy.BY_TEXT.value,
            "searchIdentifier": "Test value of searchIdentifier",
            "textToSend": "Test value of textToSend",
            "maxWait": 0.0
        }
        target = Action
        sut = DictActionConverter(source, target)

        # When
        action = sut.getConverted()

        # Then
        self.assertIsInstance(action, QuitBrowserAction)
        self.assertEqual(ActionCmd.QUIT_BROWSER, action.command)

    # ------------------------------------------------------------------------------------
    # Following tests expect Action as source and dict as target
    # ------------------------------------------------------------------------------------

    def test_actionToDict_LoadPageAction(self):
        # Given
        source = LoadPageAction(url="Test value of textToSend")
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.LOAD_PAGE.value, dataDict.get("command"))
        self.assertEqual("Test value of textToSend", dataDict.get("textToSend"))

    def test_actionToDict_SendKeysAction(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        searchConditions.searchStrategy = Strategy.BY_TEXT
        searchConditions.identifier = "Test value of searchIdentifier"
        source = SendKeysAction(searchConditions=searchConditions, text="Test value of textToSend")
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.SEND_KEYS.value, dataDict.get("command"))
        self.assertEqual(Strategy.BY_TEXT.value, dataDict.get("searchStrategy"))
        self.assertEqual("Test value of searchIdentifier", dataDict.get("searchIdentifier"))
        self.assertEqual("Test value of textToSend", dataDict.get("textToSend"))

    def test_actionToDict_ClickAction(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        searchConditions.searchStrategy = Strategy.BY_XPATH
        searchConditions.identifier = "Test value of searchIdentifier"
        source = ClickAction(searchConditions=searchConditions)
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.CLICK.value, dataDict.get("command"))
        self.assertEqual(Strategy.BY_XPATH.value, dataDict.get("searchStrategy"))
        self.assertEqual("Test value of searchIdentifier", dataDict.get("searchIdentifier"))

    def test_actionToDict_SubmitAction(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        searchConditions.searchStrategy = Strategy.BY_ID
        searchConditions.identifier = "Test value of searchIdentifier"
        source = SubmitAction(searchConditions=searchConditions)
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.SUBMIT.value, dataDict.get("command"))
        self.assertEqual(Strategy.BY_ID.value, dataDict.get("searchStrategy"))
        self.assertEqual("Test value of searchIdentifier", dataDict.get("searchIdentifier"))

    def test_actionToDict_WaitUntilVisibleAction(self):
        # Given
        searchConditions = Mock(spec_set=SearchConditions)
        searchConditions.searchStrategy = Strategy.BY_XPATH
        searchConditions.identifier = "Test value of searchIdentifier"
        source = WaitUntilVisibleAction(searchConditions=searchConditions, maxWait=44.12)
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.WAIT_UNTIL_VISIBLE.value, dataDict.get("command"))
        self.assertEqual(Strategy.BY_XPATH.value, dataDict.get("searchStrategy"))
        self.assertEqual("Test value of searchIdentifier", dataDict.get("searchIdentifier"))
        self.assertEqual(44.12, dataDict.get("maxWait"))

    def test_actionToDict_PauseAction(self):
        # Given
        source = PauseAction(seconds=-123.0)
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.PAUSE.value, dataDict.get("command"))
        self.assertEqual(-123.0, dataDict.get("maxWait"))

    def test_actionToDict_QuitBrowserAction(self):
        # Given
        source = QuitBrowserAction()
        target = dict
        sut = DictActionConverter(source, target)

        # When
        dataDict = sut.getConverted()

        # Then
        self.assertIsInstance(dataDict, dict)
        self.assertEqual(ActionCmd.QUIT_BROWSER.value, dataDict.get("command"))

