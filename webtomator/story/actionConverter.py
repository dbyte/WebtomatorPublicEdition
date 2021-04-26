# actionConverter.py
import debug.logger as clog
from typing import Optional, ClassVar

from network.searchconditions import Strategy, SearchConditions
from story.action import Action, ActionKey, ActionCmd, Searchable, \
    TextSendable, Waitable, ActionFactory
from story.baseConverter import BaseConverter

logger = clog.getLogger(__name__)


class DictActionConverter(BaseConverter):
    __CURRENT_VERSION: ClassVar[float] = 1.00

    def __init__(self, source, target):
        super().__init__(source, target, allowedTypes=(Action, dict))

    def getConverted(self):
        if self._target == Action:
            return self.__dictToAction()
        return self.__actionToDict()

    def __dictToAction(self) -> Optional[Action]:
        dataDict = self._source

        if dataDict is None:
            raise ValueError("Expected a valid dict, but got a NoneType.")

        # Create searchStrategy
        strategyStr = dataDict.get(ActionKey.SEARCH_STRATEGY.value, "")
        searchStrategy = Strategy(strategyStr) if strategyStr else Strategy.IGNORE

        # Create SearchConditions
        searchIdentifier = dataDict.get(ActionKey.SEARCH_IDENTIFIER.value, "")
        searchConditions = SearchConditions(strategy=searchStrategy,
                                            identifier=searchIdentifier)

        # Create Action
        cmd = ActionCmd(dataDict.get(ActionKey.COMMAND.value, ActionCmd.NONE.value))
        action = ActionFactory().make(forCommand=cmd,
                                      textToSend=dataDict.get(ActionKey.TEXT_TO_SEND.value, ""),
                                      searchConditions=searchConditions,
                                      maxWait=dataDict.get(ActionKey.MAX_WAIT.value, 0.0)
                                      )

        return action

    def __actionToDict(self) -> dict:
        action: Action = self._source

        if action is None:
            raise ValueError(f"Expected a valid Action, but got a NoneType.")

        dataDict = dict()

        # Set command (property is part of Action)
        dataDict[ActionKey.COMMAND.value] = action.command.value

        # Set SearchConditions if present

        dataDict[ActionKey.SEARCH_STRATEGY.value] = ""
        dataDict[ActionKey.SEARCH_IDENTIFIER.value] = ""
        if isinstance(action, Searchable):
            searchConditions = action.searchConditions
            dataDict[ActionKey.SEARCH_STRATEGY.value] = searchConditions.searchStrategy.value
            dataDict[ActionKey.SEARCH_IDENTIFIER.value] = searchConditions.identifier

        # Set textToSend if present

        dataDict[ActionKey.TEXT_TO_SEND.value] = ""
        if isinstance(action, TextSendable):
            dataDict[ActionKey.TEXT_TO_SEND.value] = action.textToSend

        # Set maxWait if present

        dataDict[ActionKey.MAX_WAIT.value] = 0.0
        if isinstance(action, Waitable):
            dataDict[ActionKey.MAX_WAIT.value] = action.maxWait

        return dataDict
