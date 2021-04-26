# story.py
import debug.logger as clog
import time
from abc import ABC
from abc import abstractmethod
from enum import Enum

from network.browser import Browser
from network.searchconditions import SearchConditions

from debug.performance import Performance, IPerformance

logger = clog.getLogger(__name__)


class ActionCmd(Enum):
    """
    Mapper for all provided types of base class "Action".
    Note: The associated numbers (values) should NEVER be renamed as they get persisted by
    saving them as JSON ActionBundle files. Further these numbers are referenced
    when converting dictionaries from/to Action.
    """

    NONE = 1, "No action"
    LOAD_PAGE = 2, "Load page"
    SEND_KEYS = 3, "Send text or keystrokes"
    CLICK = 4, "Click"
    SUBMIT = 5, "Submit"
    WAIT_UNTIL_VISIBLE = 6, "Wait until element is visible"
    PAUSE = 7, "Pause all tasks"
    QUIT_BROWSER = 8, "Quit virtual browser"
    SELECT = 9, "Select menu item"

    def __new__(cls, value, readable: str = ""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.readable = readable
        return obj


class ActionKey(Enum):
    """
    Mapper for all provided story arguments.
    Note: The associated strings should NEVER be renamed as they get persisted by saving
    them as JSON ActionBundle files. Further these strings are referenced
    when converting dictionaries from/to Action.
    """

    NONE = "none", "None"
    COMMAND = "command", "Command"
    SEARCH_STRATEGY = "searchStrategy", "Search strategy"
    SEARCH_IDENTIFIER = "searchIdentifier", "Search identifier"
    TEXT_TO_SEND = "textToSend", "Text to send"
    MAX_WAIT = "maxWait", "Maximum waiting time (sec.)"

    def __new__(cls, value, readable: str = ""):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.readable = readable
        return obj


class Action(ABC):
    """
    Abstract base class that all action implementations must inherit from.
    """

    __command: ActionCmd

    @property
    def command(self) -> ActionCmd:
        return self.__command

    @command.setter
    def command(self, value: ActionCmd):
        self.__command = value

    @abstractmethod
    def execute(self, browser: Browser):
        raise NotImplementedError("Implement this method in the inherited class.")


class TextSendable(Action, ABC):
    __textToSend: str

    @property
    def textToSend(self) -> str:
        return self.__textToSend

    @textToSend.setter
    def textToSend(self, value: str):
        self.__textToSend = value


class Searchable(Action, ABC):
    __searchConditions: SearchConditions

    @property
    def searchConditions(self) -> SearchConditions:
        return self.__searchConditions

    @searchConditions.setter
    def searchConditions(self, value: SearchConditions):
        self.__searchConditions = value


class Waitable(Action, ABC):
    __maxWait: float

    @property
    def maxWait(self) -> float:
        return self.__maxWait

    @maxWait.setter
    def maxWait(self, value: float):
        self.__maxWait = value


class ActionProxy(Action):
    """
    We can do some stuff before and after main execution here, like logging.
    Note it's still allowed to call the actions directly (without this proxy).
    Call like: ActionProxy(SendKeysAction(...)).execute(browser)
    """

    def __init__(self, impl: Action, performance: IPerformance = Performance()):
        self.__impl = impl
        self.__performance = performance

    def execute(self, browser: Browser):
        className = self.__impl.__class__.__name__
        logger.info("Executing %s...", className)
        self.__performance.setTimeMarker()
        self.__impl.execute(browser)
        logger.info("Completed %s %s",
                    className, self.__performance.getInfo())


class NoAction(Action):
    """ A concrete Action implementation for an action placeholder.
    """
    def __init__(self):
        super().__init__()
        self.command: ActionCmd = ActionCmd.NONE

    def execute(self, browser: Browser):
        pass


class LoadPageAction(TextSendable):
    """ A concrete Action implementation.
    """

    def __init__(self, url: str):
        super().__init__()
        self.command: ActionCmd = ActionCmd.LOAD_PAGE
        self.textToSend: str = url

    def execute(self, browser: Browser):
        browser.loadInitialPage(self.textToSend)


class SendKeysAction(TextSendable, Searchable):
    """ A concrete Action implementation.
    """

    def __init__(self, searchConditions: SearchConditions, text: str):
        super().__init__()
        self.command: ActionCmd = ActionCmd.SEND_KEYS
        self.searchConditions = searchConditions
        self.textToSend = text

    def execute(self, browser: Browser):
        browser.sendKeys(self.searchConditions, self.textToSend)


class SelectAction(TextSendable, Searchable):
    """ A concrete Action implementation.
    """

    def __init__(self, searchConditions: SearchConditions, text: str):
        super().__init__()
        self.command: ActionCmd = ActionCmd.SELECT
        self.searchConditions = searchConditions
        self.textToSend = text

    def execute(self, browser: Browser):
        browser.select(self.searchConditions, self.textToSend)


class ClickAction(Searchable):
    """ A concrete Action implementation.
    """

    def __init__(self, searchConditions: SearchConditions):
        super().__init__()
        self.command: ActionCmd = ActionCmd.CLICK
        self.searchConditions = searchConditions

    def execute(self, browser: Browser):
        browser.click(self.searchConditions)


class SubmitAction(Searchable):
    """ A concrete Action implementation.
    """

    def __init__(self, searchConditions: SearchConditions):
        super().__init__()
        self.command: ActionCmd = ActionCmd.SUBMIT
        self.searchConditions = searchConditions

    def execute(self, browser: Browser):
        browser.submit(self.searchConditions)


class WaitUntilVisibleAction(Waitable, Searchable):
    """ A concrete Action implementation.
    """

    def __init__(self, searchConditions: SearchConditions, maxWait=3.0):
        super().__init__()
        self.command: ActionCmd = ActionCmd.WAIT_UNTIL_VISIBLE
        self.searchConditions = searchConditions
        self.maxWait = maxWait

    def execute(self, browser: Browser):
        browser.waitForElement(self.searchConditions, self.maxWait)


class PauseAction(Waitable):
    """ A concrete Action implementation.
    """

    def __init__(self, seconds: float):
        super().__init__()
        self.command: ActionCmd = ActionCmd.PAUSE
        self.maxWait = seconds

    def execute(self, browser: Browser):
        time.sleep(self.maxWait)


class QuitBrowserAction(Action):
    """ A concrete Action implementation.
    """

    def __init__(self):
        super().__init__()
        self.command: ActionCmd = ActionCmd.QUIT_BROWSER

    def execute(self, browser: Browser):
        browser.quit()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


class ActionFactory:

    def __init__(self):
        pass

    def make(self, forCommand: ActionCmd, **kwargs) -> Action:
        cmd = forCommand

        # Parameter check
        allowedKeys = ("textToSend", "searchConditions", "maxWait")
        if not set(kwargs.keys()).issubset(allowedKeys):
            raise KeyError(f"One or more key parameters are not valid."
                           f"Allowed keys: {allowedKeys} -- received keys: {kwargs.keys()}")

        # 1. Do some basic initialisation
        action: Action

        if cmd == ActionCmd.NONE:
            action = NoAction()

        elif cmd == ActionCmd.LOAD_PAGE:
            action = LoadPageAction(url="")

        elif cmd == ActionCmd.SEND_KEYS:
            action = SendKeysAction(searchConditions=SearchConditions(), text="")

        elif cmd == ActionCmd.CLICK:
            action = ClickAction(searchConditions=SearchConditions())

        elif cmd == ActionCmd.SUBMIT:
            action = SubmitAction(searchConditions=SearchConditions())

        elif cmd == ActionCmd.WAIT_UNTIL_VISIBLE:
            action = WaitUntilVisibleAction(searchConditions=SearchConditions(), maxWait=0)

        elif cmd == ActionCmd.PAUSE:
            action = PauseAction(seconds=0)

        elif cmd == ActionCmd.QUIT_BROWSER:
            action = QuitBrowserAction()

        elif cmd == ActionCmd.SELECT:
            action = SelectAction(searchConditions=SearchConditions(), text="")

        else:
            raise NotImplementedError(f"Action for {cmd} not implemented in Factory.")

        # 2. Do final setup depending on Action family
        # Note: Actions can be multi inherited, so NO elif here
        if isinstance(action, TextSendable):
            textToSend = kwargs.get("textToSend", "")
            action.textToSend = textToSend
        if isinstance(action, Searchable):
            searchConditions = kwargs.get("searchConditions", SearchConditions())
            action.searchConditions = searchConditions
        if isinstance(action, Waitable):
            maxWait = kwargs.get("maxWait", 0.0)
            action.maxWait = maxWait

        return action
