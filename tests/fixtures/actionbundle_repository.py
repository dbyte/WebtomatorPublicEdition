# fixtures.actionbundle_repository.py
from enum import Enum
from pathlib import Path

from story.actionBundleDao import JSONActionBundleDao


class JSONActionBundleDaoFixture(JSONActionBundleDao):

    __MY_ROOT = Path(__file__).parent
    JSON_REPO_BASEPATH: Path = __MY_ROOT / "../resources/userdata/actionbundles"
    assert JSON_REPO_BASEPATH.is_dir()

    class Filename(Enum):
        GOOGLE_SEARCH = "TestStory-Google.json"
        INVALID_JSON = "TestStory-Invalid.json"
        EMPTY_FILE = "TestStory-EmptyFile.json"
        EMPTY_ACTIONS = "TestStory-EmptyActions.json"
        NO_ACTIONS = "TestStory-NoActions.json"

    def __init__(self, path: str):
        super().__init__(str(path))

    def setPath(self, path: Path):
        self.connection.__path = path

    def update(self, data):
        raise NotImplementedError
