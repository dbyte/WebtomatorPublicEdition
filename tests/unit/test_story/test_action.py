# unit.test_story.test_action.py

import unittest
from unittest import mock
from unittest.mock import Mock

from network.browser import Browser
from network.searchconditions import SearchConditions
from debug.performance import Performance
from story.action import ActionCmd, ActionKey, Action, ActionProxy, LoadPageAction, \
    SendKeysAction, ClickAction, SubmitAction, WaitUntilVisibleAction, PauseAction, \
    QuitBrowserAction, NoAction, ActionFactory, SelectAction
from unit.testhelper import WebtomatorTestCase


class ActionCmdTest(WebtomatorTestCase):

    def test_ifWeKnowAllEnumCases(self):
        # Given
        sut = ActionCmd
        expectedCases = 9

        # When
        actual = sut.__len__()

        # Then
        self.assertEqual(
            expectedCases, actual,
            f"Enum {sut.__name__}: Found {actual} cases, expected"
            f" {expectedCases} cases. Check/extend all test cases for this Enum.")

    def test_ifEnumValuesAreCorrect(self):
        # Given
        sut = ActionCmd

        def errorMsg(a, b) -> str:
            return f"Enum case test result is {a}, but expected {b}"

        # When / Then
        actual = sut.NONE.value, sut.NONE.readable
        expected = 1, "No action"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.LOAD_PAGE.value, sut.LOAD_PAGE.readable
        expected = 2, "Load page"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.SEND_KEYS.value, sut.SEND_KEYS.readable
        expected = 3, "Send text or keystrokes"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.CLICK.value, sut.CLICK.readable
        expected = 4, "Click"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.SUBMIT.value, sut.SUBMIT.readable
        expected = 5, "Submit"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.WAIT_UNTIL_VISIBLE.value, sut.WAIT_UNTIL_VISIBLE.readable
        expected = 6, "Wait until element is visible"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.PAUSE.value, sut.PAUSE.readable
        expected = 7, "Pause all tasks"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.QUIT_BROWSER.value, sut.QUIT_BROWSER.readable
        expected = 8, "Quit virtual browser"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.SELECT.value, sut.SELECT.readable
        expected = 9, "Select menu item"
        self.assertEqual(expected, actual, errorMsg(actual, expected))


class ActionKeyTest(WebtomatorTestCase):

    def test_ifWeKnowAllEnumCases(self):
        # Given
        sut = ActionKey
        expectedCases = 6

        # When
        actual = sut.__len__()

        # Then
        self.assertEqual(
            expectedCases, actual,
            f"Enum {sut.__name__}: Found {actual} cases, expected"
            f" {expectedCases} cases. Check/extend all test cases for this Enum.")

    def test_ifEnumValuesAreCorrect(self):
        # Given
        sut = ActionKey

        def errorMsg(a, b) -> str:
            return f"Enum case result is '{a}', but expected '{b}'"

        # When / Then
        actual = sut.NONE.value, sut.NONE.readable
        expected = "none", "None"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.COMMAND.value, sut.COMMAND.readable
        expected = "command", "Command"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.SEARCH_STRATEGY.value, sut.SEARCH_STRATEGY.readable
        expected = "searchStrategy", "Search strategy"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.SEARCH_IDENTIFIER.value, sut.SEARCH_IDENTIFIER.readable
        expected = "searchIdentifier", "Search identifier"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.TEXT_TO_SEND.value, sut.TEXT_TO_SEND.readable
        expected = "textToSend", "Text to send"
        self.assertEqual(expected, actual, errorMsg(actual, expected))

        actual = sut.MAX_WAIT.value, sut.MAX_WAIT.readable
        expected = "maxWait", "Maximum waiting time (sec.)"
        self.assertEqual(expected, actual, errorMsg(actual, expected))


class ActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = Action

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'command')
        self.assertHasAttribute(sut, 'execute')


class ActionProxyTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = ActionProxy

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')

    def test_shouldCallExecuteOnProxyObject(self):
        # Given
        browser = Mock(spec=Browser)

        performance = Mock(spec_set=Performance)
        # We must mock method Performance().getInfo(), else unwanted exception.
        performance.getInfo.return_value = ""

        someAction = Mock(spec=["execute"])
        sut = ActionProxy(impl=someAction, performance=performance)

        # When
        sut.execute(browser)

        # Then
        someAction.execute.assert_called_once()


class NoActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = NoAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')


class LoadPageActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = LoadPageAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'textToSend')

    def test_shouldCall_loadInitialPage(self):
        # Given
        browser = Mock(spec=Browser)
        expectedURL = "https://test.url"
        sut = LoadPageAction(url=expectedURL)

        # When
        sut.execute(browser)

        # Then
        browser.loadInitialPage.assert_called_once()
        self.assertEqual(expectedURL, sut.textToSend)


class SendKeysActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = SendKeysAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'searchConditions')
        self.assertHasAttribute(sut, 'textToSend')

    def test_shouldCall_sendKeys(self):
        # Given
        browser = Mock(spec=Browser)
        searchConditions = Mock(spec=SearchConditions)
        expectedTextToSend = "Here is some test text."
        sut = SendKeysAction(searchConditions=searchConditions, text=expectedTextToSend)

        # When
        sut.execute(browser)

        # Then
        self.assertEqual(expectedTextToSend, sut.textToSend)
        browser.sendKeys.assert_called_once()
        browser.sendKeys.assert_called_with(searchConditions, expectedTextToSend)


class SelectActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = SelectAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'searchConditions')
        self.assertHasAttribute(sut, 'textToSend')

    def test_shouldCall_select(self):
        # Given
        browser = Mock(spec=Browser)
        searchConditions = Mock(spec=SearchConditions)
        expectedTextToSend = "Some visible menu text"
        sut = SelectAction(searchConditions=searchConditions, text=expectedTextToSend)

        # When
        sut.execute(browser)

        # Then
        self.assertEqual(expectedTextToSend, sut.textToSend)
        browser.select.assert_called_once()
        browser.select.assert_called_with(searchConditions, expectedTextToSend)


class ClickActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = ClickAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'searchConditions')

    def test_shouldCall_click(self):
        # Given
        browser = Mock(spec=Browser)
        searchConditions = Mock(spec=SearchConditions)
        sut = ClickAction(searchConditions=searchConditions)

        # When
        sut.execute(browser)

        # Then
        browser.click.assert_called_once()
        browser.click.assert_called_with(searchConditions)


class SubmitActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = SubmitAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'searchConditions')

    def test_shouldCall_submit(self):
        # Given
        browser = Mock(spec=Browser)
        searchConditions = Mock(spec=SearchConditions)
        sut = SubmitAction(searchConditions=searchConditions)

        # When
        sut.execute(browser)

        # Then
        browser.submit.assert_called_once()
        browser.submit.assert_called_with(searchConditions)


class WaitUntilVisibleActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = WaitUntilVisibleAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'searchConditions')
        self.assertHasAttribute(sut, 'maxWait')

    def test_shouldCall_waitForElementText(self):
        # Given
        browser = Mock(spec=Browser)
        searchConditions = Mock(spec=SearchConditions)
        expectedMaxWait = 1.0
        sut = WaitUntilVisibleAction(searchConditions=searchConditions, maxWait=expectedMaxWait)

        # When
        sut.execute(browser)

        # Then
        self.assertEqual(sut.maxWait, expectedMaxWait)
        browser.waitForElement.assert_called_once()
        browser.waitForElement.assert_called_with(searchConditions, expectedMaxWait)


class PauseActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = PauseAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')
        self.assertHasAttribute(sut, 'maxWait')

    def test_shouldCall_pause(self):
        # Given
        browser = Mock(spec=Browser)
        expectedMaxWait = 0.7
        sut = PauseAction(seconds=expectedMaxWait)

        # When
        with mock.patch('time.sleep', autospec=True) as sleeper:
            sut.execute(browser)

        # Then
        self.assertEqual(expectedMaxWait, sut.maxWait)
        sleeper.assert_called_once()
        sleeper.assert_called_with(expectedMaxWait)


class QuitBrowserActionTest(WebtomatorTestCase):

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = QuitBrowserAction

        # Then
        # Check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'execute')

    def test_shouldCall_quit(self):
        # Given
        browser = Mock(spec=Browser)
        sut = QuitBrowserAction()

        # When
        sut.execute(browser)

        # Then
        browser.quit.assert_called_once()


# -----------------------------------------------------------------------------
# Factory tests
# -----------------------------------------------------------------------------


class ActionFactoryTest(WebtomatorTestCase):
    sut: ActionFactory

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.sut = ActionFactory()

    @classmethod
    def tearDownClass(cls):
        del cls.sut
        super().tearDownClass()

    def test_make_shouldRaiseOnInvalidCommandParameter(self):
        # Given
        invalidCmd = Mock(spec=ActionCmd)

        # When / Then
        with self.assertRaises(NotImplementedError):
            self.sut.make(forCommand=invalidCmd)

    def test_make_shouldRaiseOnInvalidKwargs(self):
        # Given
        validCmd = ActionCmd.NONE
        validSearchConditions = Mock(spec=SearchConditions)

        # When / Then
        with self.assertRaises(KeyError):
            self.sut.make(forCommand=validCmd, something="unimportant")

        # When / Then
        with self.assertRaises(KeyError):
            self.sut.make(forCommand=validCmd,
                          searchConditions=validSearchConditions,
                          invalidArgumentKey="unimportant")

    def test_make_noneAction(self):
        # Given
        cmd = ActionCmd.NONE

        # When
        action = self.sut.make(forCommand=cmd)
        # Then
        self.assertIsInstance(action, NoAction)

    def test_make_LoadPageAction(self):
        # Given
        cmd = ActionCmd.LOAD_PAGE
        expectedTextToSend = "https://something.de"

        # When
        action = self.sut.make(forCommand=cmd,
                               textToSend=expectedTextToSend
                               )
        # Then
        self.assertIsInstance(action, LoadPageAction)
        self.assertEqual(expectedTextToSend, action.textToSend)

    def test_make_SendKeysAction(self):
        # Given
        cmd = ActionCmd.SEND_KEYS
        expectedTextToSend = "Some text here"
        expectedSearchConditions = Mock(spec=SearchConditions)

        # When
        action = self.sut.make(forCommand=cmd,
                               searchConditions=expectedSearchConditions,
                               textToSend=expectedTextToSend
                               )
        # Then
        self.assertIsInstance(action, SendKeysAction)
        self.assertEqual(expectedSearchConditions, action.searchConditions)
        self.assertEqual(expectedTextToSend, action.textToSend)

    def test_make_ClickAction(self):
        # Given
        cmd = ActionCmd.CLICK
        expectedSearchConditions = Mock(spec=SearchConditions)

        # When
        action = self.sut.make(forCommand=cmd,
                               searchConditions=expectedSearchConditions
                               )
        # Then
        self.assertIsInstance(action, ClickAction)
        self.assertEqual(expectedSearchConditions, action.searchConditions)

    def test_make_SubmitAction(self):
        # Given
        cmd = ActionCmd.SUBMIT
        expectedSearchConditions = Mock(spec=SearchConditions)

        # When
        action = self.sut.make(forCommand=cmd,
                               searchConditions=expectedSearchConditions
                               )
        # Then
        self.assertIsInstance(action, SubmitAction)
        self.assertEqual(expectedSearchConditions, action.searchConditions)

    def test_make_SelectAction(self):
        # Given
        cmd = ActionCmd.SELECT
        expectedSearchConditions = Mock(spec=SearchConditions)
        expectedTextToSend = "Some menu text to select"

        # When
        action = self.sut.make(forCommand=cmd,
                               searchConditions=expectedSearchConditions,
                               textToSend=expectedTextToSend
                               )
        # Then
        self.assertIsInstance(action, SelectAction)
        self.assertEqual(expectedSearchConditions, action.searchConditions)
        self.assertEqual(expectedTextToSend, action.textToSend)

    def test_make_waitUntilVisibleAction(self):
        # Given
        cmd = ActionCmd.WAIT_UNTIL_VISIBLE
        expectedSearchConditions = Mock(spec=SearchConditions)
        expectedMaxWait = 0.75

        # When
        action = self.sut.make(forCommand=cmd,
                               searchConditions=expectedSearchConditions,
                               maxWait=expectedMaxWait
                               )
        # Then
        self.assertIsInstance(action, WaitUntilVisibleAction)
        self.assertEqual(expectedSearchConditions, action.searchConditions)
        self.assertEqual(expectedMaxWait, action.maxWait)

    def test_make_pauseAction(self):
        # Given
        cmd = ActionCmd.PAUSE
        expectedMaxWait = 0.75

        # When
        action = self.sut.make(forCommand=cmd,
                               maxWait=expectedMaxWait
                               )
        # Then
        self.assertIsInstance(action, PauseAction)
        self.assertEqual(expectedMaxWait, action.maxWait)

    def test_make_quitBrowserAction(self):
        # Given
        cmd = ActionCmd.QUIT_BROWSER

        # When
        action = self.sut.make(forCommand=cmd)

        # Then
        self.assertIsInstance(action, QuitBrowserAction)


if __name__ == '__main__':
    unittest.main()
