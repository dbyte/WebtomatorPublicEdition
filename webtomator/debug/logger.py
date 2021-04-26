# logger.py
# -----------------------------------------------------------------------
# This logger should be used application wide.
# Import this module as early as possible in the app's startup phase!
# -----------------------------------------------------------------------
"""Custom Logging. All imports should use this instead of import builtin logging"""
from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Union
    from config.base import LoggerConfig

# Map standard's lib log levels
NOTSET = logging.NOTSET  # 0
DEBUG = logging.DEBUG  # 10
DEBUG_CONN = 15  # custom log level
INFO = logging.INFO  # 20
WARN = logging.WARN  # 30
ERROR = logging.ERROR  # 40
CRITICAL = logging.CRITICAL  # 50

logging.addLevelName(DEBUG_CONN, 'DEBUG_CONN')
Handler = logging.Handler  # typealias - forwarding to consumers


class CustomLogger(logging.Logger):
    """Custom Logging class"""

    def __init__(self, name: str, level=NOTSET):
        super().__init__(name=name, level=level)

    def debugConn(self, msg, *args, **kwargs):
        if self.isEnabledFor(DEBUG_CONN):
            self._log(DEBUG_CONN, msg, args, **kwargs)

    def addHandlers(self, *handlers: logging.Handler):
        """ Convenience method for adding more than one Handler at a time.
        Does the same as built-in `addHandler` but with multiple Handler objects.

        :param handlers: Variadic logging.Handler objects
        :return: None
        """
        [self.addHandler(handler) for handler in handlers]

# -------------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------------


def getLogger(name=None) -> CustomLogger:
    """Build a logger with the given name and returns the logger.
    This method uses the builtin logging package and we should use it instead of logging.getLogger.

    :param name: The name for the logger. This is usually the module name, ``__name__``.
    :return: logger object
    """
    logging.setLoggerClass(CustomLogger)
    customLogger = logging.getLogger(name)
    assert isinstance(customLogger, CustomLogger)

    return customLogger


def getRootLogger() -> logging.Logger:
    logging.setLoggerClass(CustomLogger)
    return logging.getLogger()


def configureLogger(logger: Union[CustomLogger, logging.Logger],
                    config: LoggerConfig,
                    logfilePath: Path = None) -> None:
    cfg = config
    minLevel = min(cfg.consoleLogLevel, cfg.fileLogLevel)
    if minLevel <= 0:
        # If one of the logLevels is 0 or less, ignore it and set the other logLevel.
        minLevel = max(cfg.consoleLogLevel, cfg.fileLogLevel)

    # Set main log level
    logger.setLevel(minLevel)

    if cfg.isConsoleLogging:
        if cfg.consoleLogLevel >= ERROR:
            logger.addHandler(ErrorAndAboveStreamHandler())

        elif cfg.consoleLogLevel >= WARN:
            logger.addHandler(WarnAndAboveStreamHandler())

        elif cfg.consoleLogLevel >= INFO:
            logger.addHandler(InfoOnlyStreamHandler())
            logger.addHandler(WarnAndAboveStreamHandler())

        elif cfg.consoleLogLevel >= DEBUG:
            logger.addHandler(DebugOnlyStreamHandler())
            logger.addHandler(InfoOnlyStreamHandler())
            logger.addHandler(WarnAndAboveStreamHandler())

    if cfg.isFileLogging:
        if not logfilePath:
            raise ValueError("File logging is activated - expected a file log path.")

        if cfg.fileLogLevel >= ERROR:
            logger.addHandler(ErrorAndAboveFileHandler(path=logfilePath))

        elif cfg.fileLogLevel >= WARN:
            logger.addHandler(WarnAndAboveFileHandler(path=logfilePath))

        elif cfg.fileLogLevel >= INFO:
            logger.addHandler(InfoOnlyFileHandler(path=logfilePath))
            logger.addHandler(WarnAndAboveFileHandler(path=logfilePath))

        elif cfg.fileLogLevel >= DEBUG:
            logger.addHandler(DebugOnlyFileHandler(path=logfilePath))
            logger.addHandler(InfoOnlyFileHandler(path=logfilePath))
            logger.addHandler(WarnAndAboveFileHandler(path=logfilePath))

# -------------------------------------------------------------------------
# Filters
# -------------------------------------------------------------------------


class LessThanLevelFilter(logging.Filter):
    def __init__(self, exclusive_maximum: int, name=""):
        super(LessThanLevelFilter, self).__init__(name)
        self.max_level = exclusive_maximum

    # Overriding parent's filter method
    def filter(self, record):
        # Non-zero return means that this message will pass.
        return True if record.levelno < self.max_level else False

# -------------------------------------------------------------------------
# Stream Handlers
# -------------------------------------------------------------------------


class DebugOnlyStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(DEBUG)
        self.addFilter(LessThanLevelFilter(INFO))


class InfoOnlyStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)

        fmt = FormatterFactory().make(BasicFormatter)
        self.setFormatter(fmt)
        self.setLevel(INFO)
        self.addFilter(LessThanLevelFilter(WARN))


class DebugAndInfoStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stdout)

        fmt = FormatterFactory().make(BasicFormatter)
        self.setFormatter(fmt)
        self.setLevel(DEBUG)
        self.addFilter(LessThanLevelFilter(WARN))


class WarnAndAboveStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stderr)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(WARN)


class ErrorAndAboveStreamHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stderr)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(ERROR)

# -------------------------------------------------------------------------
# File Handlers
# -------------------------------------------------------------------------


class CustomFileHandler(logging.FileHandler):
    def __init__(self, path: Path):

        # First! Create dir and empty log file if not exist.
        if not path.parent.is_dir():
            try:
                path.parent.mkdir()

            except Exception:
                print(f"Unable to create log directory for path {path.parent}")
                raise

        if not path.is_file():
            try:
                path.touch()

            except Exception:
                print(f"Unable to create log file with path {path}")
                raise

        super().__init__(str(path), encoding="utf-8")


class DebugOnlyFileHandler(CustomFileHandler):
    def __init__(self, path: Path):
        super().__init__(path)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(DEBUG)
        self.addFilter(LessThanLevelFilter(INFO))


class InfoOnlyFileHandler(CustomFileHandler):
    def __init__(self, path: Path):
        super().__init__(path)

        fmt = FormatterFactory().make(BasicFormatter)
        self.setFormatter(fmt)
        self.setLevel(INFO)
        self.addFilter(LessThanLevelFilter(WARN))


class DebugAndInfoFileHandler(CustomFileHandler):
    def __init__(self, path: Path):
        super().__init__(path)

        fmt = FormatterFactory().make(BasicFormatter)
        self.setFormatter(fmt)
        self.setLevel(DEBUG)
        self.addFilter(LessThanLevelFilter(WARN))


class WarnAndAboveFileHandler(CustomFileHandler):
    def __init__(self, path: Path):
        super().__init__(path)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(WARN)


class ErrorAndAboveFileHandler(CustomFileHandler):
    def __init__(self, path: Path):
        super().__init__(path)

        fmt = FormatterFactory().make(DetailedFormatter)
        self.setFormatter(fmt)
        self.setLevel(ERROR)

# -------------------------------------------------------------------------
# Formatter
# -------------------------------------------------------------------------


class BasicFormatter(logging.Formatter):
    def __init__(self):
        formatStr = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
        super().__init__(fmt=formatStr, datefmt=None, style="%")


class DetailedFormatter(logging.Formatter):
    def __init__(self):
        formatStr = "%(asctime)s [%(levelname)s] [%(name)s, %(funcName)s, %(lineno)s] %(message)s"
        super().__init__(fmt=formatStr, datefmt=None, style="%")


class FormatterFactory:
    @property
    def validFormatterTypes(self) -> tuple:
        # Extend here for any new formatter:
        return (BasicFormatter,
                DetailedFormatter)

    def make(self, formatterType) -> logging.Formatter:
        try:
            if formatterType in self.validFormatterTypes:
                return formatterType()
            else:
                raise TypeError(f"Type {formatterType} does not participate in Formatter Factory.")

        except TypeError as e:
            logging.error(e, exc_info=True, stack_info=True)
            raise
