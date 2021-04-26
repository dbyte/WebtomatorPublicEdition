# test_actionbundle.py

import unittest
from unittest import mock
from unittest.mock import Mock

from selenium.common.exceptions import WebDriverException

from network.browser import Browser
from story.action import Action
from story.actionBundle import ActionBundle
from unit.testhelper import WebtomatorTestCase


class ActionBundleTest(WebtomatorTestCase):

    __nullBrowser: Mock

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.__nullBrowser = Mock(spec=Browser)

    @classmethod
    def tearDownClass(cls):
        del cls.__nullBrowser
        super().tearDownClass()

    def test_actionBundle_shouldReturnValidActions(self):
        # Given
        action1 = Mock(spec=Action)
        action1.name = "mock 1 name"
        action2 = Mock()
        action2.name = "mock 2 name"

        # When
        sut = ActionBundle(name="some", actions=[action1, action2])

        # Then
        self.assertEqual("mock 1 name", sut.actions[0].name)
        self.assertEqual("mock 2 name", sut.actions[1].name)

    def test_name_shouldReturnValidValue(self):
        # Given
        expectedName = "This is a test name"

        # When
        sut = ActionBundle(name=expectedName, actions=[])

        # Then
        self.assertEqual(expectedName, sut.name)

    def test_createNew_shouldCreateValidActionBundle(self):
        # Given
        expectedName = "New"

        # When
        sut = ActionBundle.createNew()

        # Then
        self.assertEqual(expectedName, sut.name)
        self.assertEqual(0, len(sut.actions))

    def test_run_withValidDataShouldLoopOverActions(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        action2 = Mock(spec=[Action, 'execute'])
        action3 = Mock(spec=[Action, 'execute'])
        sut = ActionBundle(name="A test Actionbundle name", actions=[action1, action2, action3])

        # When
        sut.run(browser=self.__nullBrowser)

        # Then
        action1.execute.assert_called_once()
        action2.execute.assert_called_once()
        action3.execute.assert_called_once()

    def test_run_shouldCallProxyInsteadOfDirectCall(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        sut = ActionBundle(name="A test Actionbundle name", actions=[action1])

        with mock.patch('story.actionBundle.ActionProxy', autospec=True) as proxy:
            # When
            sut.run(browser=self.__nullBrowser)

            # Then
            proxy(action1).execute.assert_called_once()
            action1.execute.assert_not_called()

    def test_run_withZeroActionsShouldDoNothing(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        sut = ActionBundle(name="Actionbundle without actions", actions=[])

        # When
        sut.run(browser=self.__nullBrowser)

        # Then
        action1.execute.assert_not_called()

    def test_run_withNoneActionsShouldDoNothing(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        # noinspection PyTypeChecker
        sut = ActionBundle(name="Actionbundle without actions", actions=None)

        # When
        sut.run(browser=self.__nullBrowser)

        # Then
        action1.execute.assert_not_called()

    def test_run_shouldCallbackIfCallbackMethodIsGiven(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        action2 = Mock(spec=[Action, 'execute'])
        myCallback = Mock(spec=["action"])
        expectedCallbackArgs = [mock.call(action1), mock.call(action2)]
        sut = ActionBundle(name="A callback Actionbundle", actions=[action1, action2])

        # When
        sut.run(browser=self.__nullBrowser, callback=lambda action: myCallback(action))

        # Then
        # Two actions were configured in this test, so we expect 2 callbacks
        self.assertEqual(2, myCallback.call_count)
        # Expect that configured test-actions get passed back along with the callback
        self.assertEqual(expectedCallbackArgs, myCallback.call_args_list)

    def test_run_shouldStopLoopWhenReceivedStopSignal(self):
        # Given
        action1 = Mock(spec=[Action, 'execute'])
        action2 = Mock(spec=[Action, 'execute'])
        sut = ActionBundle(name="A callback Actionbundle", actions=[action1, action2])

        def stopImmediately():
            sut.stop()

        # When
        sut.run(browser=self.__nullBrowser, callback=lambda _: stopImmediately())

        # Then
        # Two actions were configuration in this test but we called stop after the
        # first callback and expect the 2nd action not to be called at all.
        action2.execute.assert_not_called()

    def test_run_shouldRaiseOnWebDriverException(self):
        # Given
        action = Mock(spec=[Action, 'execute', 'command'])
        action.command.readable.return_value = "Mocked action command"
        action.execute.side_effect = WebDriverException("This is a mocked exception.")
        sut = ActionBundle(name="A failing Actionbundle", actions=[action])

        # When / Then
        with self.assertRaises(WebDriverException):
            sut.run(browser=self.__nullBrowser)

    def test_run_shouldRaiseOnException(self):
        # Given
        action = Mock(spec=['execute', 'command'])
        action.command.readable.return_value = "Mocked action command"
        action.execute.side_effect = Exception("This is a mocked exception.")
        sut = ActionBundle(name="A failing Actionbundle", actions=[action])

        # When / Then
        with self.assertRaises(Exception):
            sut.run(browser=self.__nullBrowser)


if __name__ == '__main__':
    unittest.main()
