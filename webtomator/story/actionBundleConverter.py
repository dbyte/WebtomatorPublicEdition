# actionBundleConverter.py
from typing import List, ClassVar

import debug.logger as clog
from story.action import Action
from story.actionBundle import ActionBundle
from story.actionConverter import DictActionConverter
from story.baseConverter import BaseConverter

logger = clog.getLogger(__name__)


class DictActionBundleConverter(BaseConverter):
    __CURRENT_VERSION: ClassVar[float] = 1.00

    def __init__(self, source, target, table: str):
        super().__init__(source, target, allowedTypes=(ActionBundle, dict))
        self.__tableName: str = table

    def getConverted(self):
        if self._target == ActionBundle:
            return self.__dictToActionBundle()
        return self.__actionBundleToDict()

    def __dictToActionBundle(self) -> ActionBundle:
        dataDict = self._source
        # We don't want to stall the app in case of missing/wrong directories/files.
        # So we just return an empty ActionBundle if for some reason there is no JSON data:
        if dataDict is None or not dataDict.get("actions") or len(dataDict.get("actions")) == 0:
            return ActionBundle.createNew()

        # Convert
        action: Action
        actions: [Action] = []

        try:
            for actionDict in dataDict.get("actions"):
                action = DictActionConverter(source=actionDict, target=Action).getConverted()
                if isinstance(action, Action):
                    actions.append(action)

            actionBundle = ActionBundle(name=dataDict['name'], actions=actions)
            return actionBundle
        except KeyError:
            logger.warning("Key of actionDict could not be mapped.", exc_info=True)
            return ActionBundle.createNew()
        except Exception as e:
            logger.error("Unexpected exception. %s", e, exc_info=True)
            raise

    def __actionBundleToDict(self) -> dict:
        bundle: ActionBundle = self._source
        dictActions: List = []
        bundleName = bundle.name

        try:
            for action in bundle.actions:
                dictAction: dict = DictActionConverter(source=action, target=dict).getConverted()
                dictActions.append(dictAction.copy())
                dictAction.clear()
        except KeyError:
            logger.error("Key of actionDict could not be mapped.", exc_info=True)
            bundleName = "New"
            dictActions = []
        except Exception as e:
            logger.error("Unexpected exception.%s", e, exc_info=True)
            raise

        # Return a valid dictionary at any case except a previous raise.
        finalDict: dict = {
            "version": self.__CURRENT_VERSION,
            "name": bundleName,
            "actions": dictActions
        }

        return finalDict
