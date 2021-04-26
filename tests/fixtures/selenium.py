# selenium.py

import os
import platform
from pathlib import Path

from selenium import webdriver

from network.browser import Browser


class BrowserDriverPathFixture:

    @staticmethod
    def CHROME():
        _MY_PARENT_DIR = Path(__file__).parent

        if platform.system() == "Windows":
            path = Path(_MY_PARENT_DIR, "../../userdata/webdrivers-windows/chromedriver.exe").resolve()
            assert path.is_file()
            return str(path)

        elif platform.system() == "Darwin":
            path = Path("/usr/local/bin/chromedriver").resolve()
            assert path.is_file()
            return str(path)

        else:
            raise NotImplementedError(f"Webdriver not yet implemented for system {platform.system()}.")


class ChromeDriverFixture(webdriver.Chrome):
    chromeDriverPath: os.path

    def __init__(self, isHeadless: bool):
        chromeDriverPath = BrowserDriverPathFixture.CHROME()
        chromeOptions = webdriver.ChromeOptions()
        if isHeadless: chromeOptions.add_argument("--headless")
        super().__init__(executable_path=chromeDriverPath, options=chromeOptions)


class ChromeBrowserFixture(Browser):

    def __init__(self, isHeadless: bool):
        chromeDriver = ChromeDriverFixture(isHeadless=isHeadless)
        super().__init__(chromeDriver)

