# actionBundle.py
import debug.logger as clog
from typing import Optional, List

from selenium.common.exceptions import WebDriverException

from story.action import Action, ActionProxy
from network.browser import BrowserFactory, Browser
from debug.performance import Performance, IPerformance

logger = clog.getLogger(__name__)


class ActionBundle:

    __name: str
    __actions: List[Action]
    __stopRunning: bool

    def __init__(self, name: str, actions: List[Action]):
        self.__name = name
        if actions is None:
            self.__actions = []
        else:
            self.__actions = actions
        self.__stopRunning = False

    @property
    def name(self) -> str:
        return self.__name

    @property
    def actions(self) -> List[Action]:
        return self.__actions

    def run(self, browser: Optional[Browser] = None,
            callback: callable = None,
            performance: IPerformance = Performance()):

        # First check if we can return early
        if len(self.actions) == 0:
            logger.info("ActionBundle has 0 actions to run.")
            return

        # Reset state
        self.__stopRunning = False

        # Init and start a browser if none was given, keeping a reference to it
        if browser is None:
            logger.debug("No browser given, creating default browser.")
            browser = BrowserFactory.createDefaultBrowser(isHeadless=False)

        logger.info("Running ActionBundle \"%s\"...", self.name)
        performance.setTimeMarker()

        for action in self.actions:
            # Callback if registered and handover current action object.
            if callback:
                logger.debug("Callback to %s", callback)
                callback(action)

            if self.__stopRunning:
                self.__stopRunning = False
                logger.debug("Received stop request")
                browser.quit()
                break

            # Execute action.
            # Do not use action.execute(browser) directly, instead use the dedicated proxy:
            try:
                ActionProxy(action).execute(browser)

            except WebDriverException as e:
                logger.warning("WebDriver error. Action '%s' failed. Stopping ActionBundle.",
                               action.command.readable)
                browser.quit()
                raise e

            except Exception as e:
                logger.warning("An error occurred. Action '%s' failed. Stopping ActionBundle.",
                               action.command.readable)
                browser.quit()
                raise e

        logger.info("Finished ActionBundle \"%s\" %s", self.name, performance.getInfo())

    def stop(self):
        """Hook to stop execution (a.k.a the run(...) loop) from outside.
        """
        self.__stopRunning = True

    @classmethod
    def createNew(cls):
        # Create a fresh new ActionBundle with empty action array
        return ActionBundle(name="New", actions=[])
