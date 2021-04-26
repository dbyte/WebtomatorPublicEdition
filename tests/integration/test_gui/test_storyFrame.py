# integration.test_gui.test_storyFrame.py
import pathlib as pl

from fixtures.actionbundle_repository import JSONActionBundleDaoFixture
from story.actionBundle import ActionBundle
from story.actionBundleDao import JSONActionBundleDao
from unit.testhelper import WebtomatorTestCase


class TestBaseWindow(WebtomatorTestCase):

    browser = None
    dao: JSONActionBundleDaoFixture
    defaultActionBundleRepoPath: pl.Path

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.defaultActionBundleRepoPath = \
            JSONActionBundleDaoFixture.JSON_REPO_BASEPATH

    @classmethod
    def tearDownClass(cls):
        del cls.defaultActionBundleRepoPath
        super().tearDownClass()

    def test_init_shouldDisplayValidStory(self):
        # Given
        filename = JSONActionBundleDaoFixture.Filename.GOOGLE_SEARCH.value
        with JSONActionBundleDao(str(self.defaultActionBundleRepoPath / filename)) as dao:
            bundle: ActionBundle = dao.loadAll()

        # When

        # Then
