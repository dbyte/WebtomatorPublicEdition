# test_actionbundle.py

import unittest
import pathlib as pl

from fixtures.actionbundle_repository import JSONActionBundleDaoFixture
from fixtures.selenium import ChromeBrowserFixture
from story.actionBundle import ActionBundle
from story.actionBundleDao import JSONActionBundleDao
from unit.testhelper import WebtomatorTestCase


class TestActionBundle(WebtomatorTestCase):
    browser = None
    defaultActionBundleRepoPath: pl.Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.browser = ChromeBrowserFixture(isHeadless=True)
        cls.defaultActionBundleRepoPath = \
            JSONActionBundleDaoFixture.JSON_REPO_BASEPATH

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        del cls.browser, cls.defaultActionBundleRepoPath
        super().tearDownClass()

    def test_run_withValidJSONDataStore(self):
        # Given
        filename = JSONActionBundleDaoFixture.Filename.GOOGLE_SEARCH.value
        path = self.defaultActionBundleRepoPath / filename
        with JSONActionBundleDao(str(path)) as dao:
            sut: ActionBundle = dao.loadAll()

        # When
        sut.run(browser=self.browser)


if __name__ == '__main__':
    unittest.main()
