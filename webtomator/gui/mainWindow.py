# gui.mainWindow.py
import pathlib as pl
import sys

from PyQt5 import uic, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QBrush, QColor, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication, QTableWidgetItem, QFileDialog, \
    QTableWidget, QHeaderView, QComboBox, QPushButton

import debug.logger as clog
from network.browser import BrowserFactory
from story.action import ActionKey, TextSendable, Waitable, Searchable
from story.actionBundle import ActionBundle
from story.actionBundleDao import JSONActionBundleDao

logger = clog.getLogger(__name__)


class MainWindowController(QMainWindow):
    __storyData: ActionBundle
    # Type hints for .ui objects - same name, do not change here!
    storyStatementList: QTableWidget
    comboLogLevel: QComboBox
    btnPlay: QPushButton
    btnLoadStory: QPushButton
    btnSaveStory: QPushButton
    # Signals
    sigStoryDataChanged = pyqtSignal()  # Must NOT be in constructor !

    @property
    def storyData(self):
        return self.__storyData

    @storyData.setter
    def storyData(self, bundle: ActionBundle):
        self.__storyData = bundle
        self.sigStoryDataChanged.emit()

    def __init__(self, *args, **kwargs):
        logger.debug("Initializing class %s", __class__.__name__)

        # Order of steps is important from here.

        # 1. Load UI file
        super(MainWindowController, self).__init__(*args, **kwargs)
        uic.loadUi("mainWindow.ui", self)  # Loads all widgets of .ui into my instance

        # 2. Init priority properties
        # Set StoryLogHandler which is responsible for logging into a GUI-Widget
        self.storyLogHandler = StoryLogHandler()
        # Thread handling. We later need to access the worker while running,
        # to be able to force stop it. So preserve window lifecycle.
        self.storyWorker = None
        # Keep thread lifecycle, so we don't need to create any new as long as this window lives
        self.workerThread = QThread()

        # Bind GUI elements.
        self.defineConnections()

        # 3. Init general properties which may depend on step 2.
        self.storyData = ActionBundle.createNew()

        # 4. Init UI
        self.initView()

    def initView(self):
        self.setStoryStatementListLayout()
        self.initProgressbar(isVisible=False)
        self.defineComboLogLevel()
        self.btnPlay.setShortcut(QKeySequence("Ctrl+R"))
        self.btnLoadStory.setShortcut(QKeySequence("Ctrl+L"))
        self.btnSaveStory.setShortcut(QKeySequence("Ctrl+S"))

    def defineConnections(self):
        self.storyLogHandler.sigLoggerEmitted.connect(self.addLogText)
        self.sigStoryDataChanged.connect(self.setRunButtonState)
        self.sigStoryDataChanged.connect(self.setStoryTitle)
        self.sigStoryDataChanged.connect(self.setStoryStatementListData)
        self.btnLoadStory.clicked.connect(self.onClickedLoadStory)
        self.btnPlay.clicked.connect(self.onClickedRun)
        self.btnClearLog.clicked.connect(self.onClickedClearLog)
        self.comboLogLevel.currentIndexChanged.connect(self.onComboLogLevelChanged)

    def addStoryLogHandlerToLogger(self, level):
        """Add dedicated log handler to some package loggers (hence all its
        children, too) for routing logs into the GUI widget.
        NOTE: We MUST NOT change log levels of the loggers themselves here!

        :param level: The log level
        :return: None
        """
        packagesToChange = (__name__, "storage", "story", "network", "selenium")
        self.storyLogHandler.setLevel(level)

        for package in packagesToChange:
            tmpLogger = clog.getLogger(package)  # Side effect: sets new logger if not exists!
            tmpLogger.removeHandler(self.storyLogHandler)  # removing only works by reference!
            tmpLogger.addHandler(self.storyLogHandler)

    def setStoryTitle(self):
        self.lblStoryTitle.setText(f"Loaded Story: {self.storyData.name}")

    def setStoryStatementListLayout(self):
        # Set style of story list
        self.storyStatementList.setShowGrid(False)
        self.storyStatementList.setStyleSheet('QTableView::item {border-right: 1px solid #d6d9dc;}')
        # Set the story headers
        headerLabels = ["Action", "Property", "Value", "Search Data", "Search Strategy", "Result"]
        self.storyStatementList.setColumnCount(len(headerLabels))
        self.storyStatementList.setHorizontalHeaderLabels(headerLabels)

        # Fonts
        headerFont = QFont()
        headerFont.setPointSize(15)
        self.storyStatementList.horizontalHeader().setFont(headerFont)
        self.storyStatementList.verticalHeader().setFont(headerFont)
        # Fit horizontal sizes
        headerH: QHeaderView = self.storyStatementList.horizontalHeader()
        headerH.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        headerH.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        headerH.setSectionResizeMode(2, QHeaderView.Interactive)
        headerH.setSectionResizeMode(3, QHeaderView.Interactive)
        headerH.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        headerH.setSectionResizeMode(5, QHeaderView.Stretch)

    def setStoryStatementListData(self):
        numberOfStatements = len(self.storyData.actions)
        self.storyStatementList.setRowCount(numberOfStatements)
        # Fill
        for row, statement in enumerate(self.storyData.actions):
            # Set cells
            # col id 0
            content = QTableWidgetItem(statement.command.readable)
            content.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.storyStatementList.setItem(row, 0, content)
            # col id 1, 2
            content = ("", "")
            if isinstance(statement, TextSendable):
                content = (ActionKey.TEXT_TO_SEND.readable, statement.textToSend)
            elif isinstance(statement, Waitable):
                content = (ActionKey.MAX_WAIT.readable, str(statement.maxWait))
            self.storyStatementList.setItem(row, 1, QTableWidgetItem(content[0]))
            self.storyStatementList.setItem(row, 2, QTableWidgetItem(content[1]))
            # col id 3, 4
            content = ("", "")
            if isinstance(statement, Searchable):
                content = (statement.searchConditions.identifier,
                           statement.searchConditions.searchStrategy.readable)
            self.storyStatementList.setItem(row, 3, QTableWidgetItem(content[0]))
            self.storyStatementList.setItem(row, 4, QTableWidgetItem(content[1]))
            # col id 5 is set by setStoryStatementIndicatorsToDefault()
            self.setStoryStatementIndicatorsToDefault()

    def setStoryStatementIndicatorsToDefault(self):
        for row, statement in enumerate(self.storyData.actions):
            # Vertical headers
            self.setStoryStatementVerticalHeader(row=row)
            # Results
            self.setStoryStatementResult(row=row, text="")

    def setStoryStatementVerticalHeader(self, row: int, rgb: (int, int, int) = None):
        if row < 0:
            return
        counterStr = str(row + 1)
        headerItem = QTableWidgetItem(counterStr)
        if rgb:
            r, g, b = rgb[0], rgb[1], rgb[2]
            brush = QBrush(QColor(r, g, b))
            headerItem.setBackground(brush)
        self.storyStatementList.setVerticalHeaderItem(row, headerItem)

    def setStoryStatementResult(self, row, text: str):
        if row < 0:
            return
        COLUMN = 5
        content = QTableWidgetItem(text)
        content.setTextAlignment(QtCore.Qt.AlignCenter)
        content.setForeground(QBrush(QColor(94, 94, 94)))
        self.storyStatementList.setItem(row, COLUMN, content)

    def defineComboLogLevel(self):
        self.comboLogLevel.disconnect()  # Avoid multiple triggers while setting up

        self.comboLogLevel.clear()
        self.comboLogLevel.addItem("Debug", clog.DEBUG)
        self.comboLogLevel.addItem("Info", clog.INFO)
        self.comboLogLevel.addItem("Warning", clog.WARN)
        self.comboLogLevel.addItem("Error", clog.ERROR)
        self.comboLogLevel.addItem("Critical", clog.CRITICAL)

        self.comboLogLevel.currentIndexChanged.connect(self.onComboLogLevelChanged)
        self.comboLogLevel.setCurrentIndex(1)

    def addLogText(self, logText):
        self.logList.appendPlainText(logText)
        self.logList.moveCursor(QtGui.QTextCursor.End)  # implies scrolling

    def initProgressbar(self, isVisible: bool, maximum: int = 100, showText: bool = False):
        if isVisible:
            self.progressBar.setMaximum(maximum)
            self.progressBar.show()
        else:
            self.progressBar.hide()
            self.setProgressbar(0)
        self.progressBar.setTextVisible(showText)

    def setProgressbar(self, val):
        self.progressBar.setValue(val)

    def setRunButtonState(self):
        savedShortcut = self.btnPlay.shortcut()  # We must restore that below
        isEnabled = len(self.storyData.actions) > 0
        self.btnPlay.setEnabled(isEnabled)
        if self.workerThread.isRunning():
            self.btnPlay.setText("Stop")
        else:
            self.btnPlay.setText("Run")
        # Documentation says: Shortcut gets deleted after setText is called. Restore:
        self.btnPlay.setShortcut(savedShortcut)

    def runStory(self):
        actionCount = len(self.storyData.actions)
        if actionCount == 0:
            return
        self.initProgressbar(isVisible=True, maximum=actionCount, showText=True)
        # Setup storyWorker & thread
        self.storyWorker = StoryWorker(self.storyData, doHeadless=True)
        self.workerThread.started.connect(self.storyWorker.work)
        self.storyWorker.sigStarted.connect(self.setRunButtonState)
        self.storyWorker.sigStarted.connect(self.setStoryStatementIndicatorsToDefault)
        self.storyWorker.sigCurrentAction.connect(self.onStoryRunNextStatement)
        self.storyWorker.sigCompleted.connect(self.onStoryRunCompleted)
        # Only delete worker object inside the thread after it's been finished work.
        # Notice: We do NOT mark the workerThread for deletion as we will reuse it.
        self.storyWorker.sigCompleted.connect(self.storyWorker.deleteLater)
        # Move worker to thread and start working:
        self.storyWorker.moveToThread(self.workerThread)  # Move Worker object to Thread object
        # Start work
        self.workerThread.start()
        self.workerThread.setPriority(QThread.HighPriority)

    def openFileDialog(self, dirPath: pl.Path) -> pl.Path:
        dirStr = ""
        if dirPath is not None and dirPath.is_dir():
            dirStr = str(dirPath)
        # Setup and show dialog
        dlg = QFileDialog()
        options = dlg.HideNameFilterDetails
        pathStr, what = dlg.getOpenFileName(
            parent=self, caption="Open a story", directory=dirStr,
            filter="Story Files (*.json);; All Files (*)",
            options=options)
        # Transform path string of selected file
        if pathStr:
            return pl.Path(pathStr)

    # ---------------------------------------------------------------------------------
    # Callbacks
    # ---------------------------------------------------------------------------------

    def onClickedLoadStory(self, _, dao=JSONActionBundleDao()):
        path = self.openFileDialog(dao.connection.path.parent)
        if path:
            try:
                dao.connection.path = path
                with dao as connectedDao:
                    self.storyData = connectedDao.loadAll()

            except Exception as e:
                logger.error("Failed to load story. %s", e, exc_info=True)

    def onClickedRun(self, _):
        if self.workerThread.isRunning():
            logger.info("User stopped story execution.")
            self.storyWorker.stop()
        else:
            self.runStory()

    def onClickedClearLog(self, _):
        self.logList.clear()

    def onComboLogLevelChanged(self):
        currentLevel = self.comboLogLevel.currentData()
        self.addStoryLogHandlerToLogger(currentLevel)
        logger.debug("Log level changed - new level: %s", currentLevel)

    def onStoryRunNextStatement(self, actionProgress: int):
        row = actionProgress - 1
        self.setStoryStatementResult(row, text="ok")
        self.setStoryStatementVerticalHeader(row, rgb=(26, 173, 102))  # mark green
        self.setProgressbar(actionProgress)

    def onStoryRunCompleted(self):
        if not self.workerThread.isRunning():
            return
        # Stop storyWorker's thread and do cleanups
        logger.debug("Work completed. Waiting for storyWorker thread to quit...")
        self.workerThread.quit()
        self.workerThread.wait()
        if self.workerThread.isFinished():
            self.initProgressbar(isVisible=False)
            self.setRunButtonState()
            logger.debug("Worker thread did quit.\n")


class StoryWorker(QObject):
    """
    Worker for running a story. Create an instance of it and move it to a thread.
    """
    __storyData: ActionBundle
    __doHeadless: bool
    __actionProgress: int

    sigStarted = pyqtSignal()  # Must NOT be in constructor !
    sigCurrentAction = pyqtSignal(int)  # dito
    sigCompleted = pyqtSignal()  # dito

    def __init__(self, storyData: ActionBundle, doHeadless: bool):
        super().__init__()
        self.__storyData = storyData
        self.__doHeadless = doHeadless
        self.__actionProgress = 0

    @pyqtSlot(name="worker")
    def work(self):
        self.sigStarted.emit()
        self.__actionProgress = 0
        browser = BrowserFactory.createDefaultBrowser(isHeadless=self.__doHeadless)
        logger.info("Story worker started")

        try:
            self.__storyData.run(browser, callback=lambda action: self.update(action))
        except Exception as e:
            logger.warning("%s", e, exc_info=True)

        logger.info("Story worker ended\n%s" % ("-" * 23))
        self.sigCompleted.emit()

    @pyqtSlot(name="stopWorker")
    def stop(self):
        self.__storyData.stop()

    @pyqtSlot(name="progressCallbackFromStory")
    def update(self, _):
        """This is a callback from self.storyData.run
        :param _: type Action, unused here
        :return: None
        """
        self.__actionProgress += 1
        self.sigCurrentAction.emit(self.__actionProgress)


class StoryLogHandler(clog.Handler, QObject):
    sigLoggerEmitted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def setLevel(self, level) -> None:
        """Override logging.Handler's setLevel() method

        :param level: The log level
        :type level: logging._Level
        :return: None
        """
        super().setLevel(level)
        if level == clog.DEBUG or level >= clog.WARN:
            detailed = clog.FormatterFactory().make(clog.DetailedFormatter)
            self.setFormatter(detailed)
        else:
            basic = clog.FormatterFactory().make(clog.BasicFormatter)
            self.setFormatter(basic)

    # Override logging.Handler's emit() method
    @pyqtSlot(name="logEmitter")
    def emit(self, record):
        """Override logging.Handler's emit() method

        :param record: The log record
        :type record: logging.Record
        :return: None
        """
        msg = self.format(record)
        # Emit pyqt signal for any listeners which connect to it (this is thread safe).
        self.sigLoggerEmitted.emit(msg)


def main():
    # This logger config should run at application entry point.
    # Level of root logger should be DEBUG here, everything else gets filtered by handlers.
    # If we set it higher, the GUI-Log-Widget will not be able to show the lower leveled logs!
    rootLogger = clog.getRootLogger()
    rootLogger.setLevel(clog.DEBUG)
    # Add console handling (fallback) for all loggers, including frameworks/libs
    rootLogger.addHandler(clog.InfoOnlyStreamHandler())
    rootLogger.addHandler(clog.WarnAndAboveStreamHandler())

    # Start GUI app
    app = QApplication(sys.argv)
    window = MainWindowController()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
