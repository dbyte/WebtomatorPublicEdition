# unit.test_story.test_actionBundleDao.py
import json
import os
import shutil
from pathlib import Path
from unittest.mock import Mock

from network.searchconditions import SearchConditions, Strategy
from fixtures.actionbundle_repository import JSONActionBundleDaoFixture
from story.action import LoadPageAction, SendKeysAction, ActionCmd
from story.actionBundle import ActionBundle
from story.actionBundleDao import JSONActionBundleDao
from unit.testhelper import WebtomatorTestCase


class JSONActionBundleDaoTest(WebtomatorTestCase):
    ACTIONBUNDLE_TEST_DIR_PATH: Path = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.ACTIONBUNDLE_TEST_DIR_PATH = \
            JSONActionBundleDaoFixture.JSON_REPO_BASEPATH

    @classmethod
    def tearDownClass(cls):
        del cls.ACTIONBUNDLE_TEST_DIR_PATH
        super().tearDownClass()

    def test_ifVitalAttributesArePresent(self):
        # Given
        sut = JSONActionBundleDao

        # Then check presence of vital public properties/methods
        self.assertHasAttribute(sut, 'loadAll')
        self.assertHasAttribute(sut, 'saveAll')
        self.assertHasAttribute(sut, 'deleteAll')
        self.assertHasAttribute(sut, 'insert')

    # ---------------------------------------------------------------------
    # JSON init tests
    # ---------------------------------------------------------------------

    def test_init_shouldSetDefaultBasePathIfGivenPathIsNone(self):
        # Given
        givenPath = None

        # When
        sut = JSONActionBundleDao(givenPath)
        actualPath = sut.connection.path

        # Then
        # Expect that the actual directory name equals "actionbundles"
        self.assertEqual("actionbundles", actualPath.name)
        # Expect that a substring of the actual path equals "/userdata/actionbundles"
        self.assertIn(str(Path("/userdata/actionbundles")), str(sut.connection.path))
        # Expect that the actual path points to existing directory
        self.assertEqual(actualPath.is_dir(), True)

    # ---------------------------------------------------------------------
    # JSON LOAD tests
    # ---------------------------------------------------------------------

    def test_loadAll_shouldRaiseIfGivenPathDoesNotPointToFile(self):
        # Given
        givenPath = "/this/is/not/a/valid/directory/file.json"
        sut = JSONActionBundleDao(givenPath)

        # When / Then
        with self.assertRaises(Exception):
            sut.loadAll()

    def test_load_shouldRaiseOnValidPathWithInvalidFilename(self):
        # Given
        path = self.ACTIONBUNDLE_TEST_DIR_PATH

        for invalidFilename in self.getInvalidFilenames():
            # When
            sut = JSONActionBundleDao(str(Path(path, invalidFilename)))
            # Then
            with self.assertRaises(Exception):
                sut.loadAll()

    def test_load_shouldReturnValidActionBundle(self):
        # Note that we are testing only basic expectations here. Conversion from
        # JSON/dict to an ActionBundle object is tested with dedicated methods within the
        # converter test classes.

        # Given
        filename = JSONActionBundleDaoFixture.Filename.GOOGLE_SEARCH.value
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / filename

        # When
        with JSONActionBundleDao(str(path)) as sut:
            actionBundle = sut.loadAll()

        # Then
        # Expect that we got back a valid ActionBundle object
        self.assertIsInstance(actionBundle, ActionBundle)
        # Expect that the ActionBundle has at least 1 action in it.
        self.assertGreaterEqual(len(actionBundle.actions), 1)

    def test_load_shouldRaiseOnInvalidFileContent(self):
        # Note that we are testing only basic expectations here. Conversion from
        # JSON/dict to an ActionBundle object is tested with dedicated methods within the
        # converter test classes.

        # Given a file with invalid structure
        filename = JSONActionBundleDaoFixture.Filename.INVALID_JSON.value
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / filename
        sut = JSONActionBundleDao(str(path))

        # When / Then
        with self.assertRaises(Exception):
            sut.loadAll()

        # Given an empty JSON file
        filename = JSONActionBundleDaoFixture.Filename.EMPTY_FILE.value
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / filename
        sut = JSONActionBundleDao(str(path))

        # When / Then
        with self.assertRaises(Exception):
            sut.loadAll()

    def test_load_shouldReturnValidActionBundleOnJSONWithoutActions(self):
        # Note that we are testing only basic expectations here. Conversion from
        # JSON/dict to an ActionBundle object is tested with dedicated methods within the
        # converter test classes.

        # Given
        filename = JSONActionBundleDaoFixture.Filename.NO_ACTIONS.value
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / filename

        # When
        with JSONActionBundleDao(str(path)) as sut:
            actionBundle = sut.loadAll()

        # Then
        # Expect that we got back a valid ActionBundle object
        self.assertIsInstance(actionBundle, ActionBundle)
        # Expect that the ActionBundle has 0 actions in it.
        self.assertEqual(0, len(actionBundle.actions))
        # Expect that the ActionBundle has a name.
        self.assertIsNot("", actionBundle.name)

    def test_load_shouldReturnValidActionBundleOnJSONWithEmptyActions(self):
        # Note that we are testing only basic expectations here. Conversion from
        # JSON/dict to an ActionBundle object is tested with dedicated methods within the
        # converter test classes.

        # Given
        filename = JSONActionBundleDaoFixture.Filename.EMPTY_ACTIONS.value
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / filename

        # When
        with JSONActionBundleDao(str(path)) as sut:
            actionBundle = sut.loadAll()

        # Then
        # Expect that we got back a valid ActionBundle object
        self.assertIsInstance(actionBundle, ActionBundle)
        # Expect that the ActionBundle has 1 action in it.
        self.assertEqual(1, len(actionBundle.actions))
        # Expect that the generated action has enum command NONE.
        self.assertEqual(ActionCmd.NONE, actionBundle.actions[0].command)
        # Expect that the ActionBundle has a name.
        self.assertIsNot("", actionBundle.name)

    # ---------------------------------------------------------------------
    # JSON SAVE tests
    # ---------------------------------------------------------------------

    def test_save_shouldPersistGivenActionBundleAsJSON(self):
        # Note that we are testing only basic expectations here. Conversion from
        # ActionBundle to JSON/dict object is tested with dedicated methods
        # within the converter test classes.

        # Given
        searchConditions = SearchConditions(strategy=Strategy.BY_XPATH, identifier="Nothing")
        action1 = LoadPageAction(url="https://test.url.de")
        action2 = SendKeysAction(searchConditions=searchConditions, text="Some test to send")
        actionBundle = ActionBundle(name="Saving test - Test story", actions=[action1, action2])
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / f"{actionBundle.name}.json"
        sut = JSONActionBundleDao(str(path))

        # Precondition: Test directory for JSON files must be present
        assert path.parent.is_dir()

        # When
        sut.connection.open()
        sut.saveAll(data=actionBundle)

        # Then
        # Expect the file was created.
        self.assertTrue(path.is_file(),
                        f"Expected file at path {path} but there is no file at this path.")

        # Expect that there is some content in the file which has the title
        # of the ActionBundle in it.
        sut.connection.db.seek(0)
        rawTextFromSavedFile = sut.connection.db.readline(300)
        sut.connection.db.close()
        self.assertIn(actionBundle.name, rawTextFromSavedFile)

        # Cleanup, remove test file.
        if path.is_file():
            path.unlink()

    def test_save_shouldRaiseWhenInvalidJSONWasGenerated(self):
        # Given
        action = Mock(spec=LoadPageAction)
        actionBundle = Mock(spec=ActionBundle)
        actionBundle.name = "Test bundle"
        actionBundle.actions = [action]
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / f"{actionBundle.name}.json"

        # When / Then
        with self.assertRaises(Exception):
            with JSONActionBundleDao(str(path)) as sut:
                sut.saveAll(data=actionBundle)

        if path.is_file():
            path.unlink()

    def test_save_shouldRaiseOnInvalidName(self):
        # Given
        dirPath = self.ACTIONBUNDLE_TEST_DIR_PATH

        for invalidName in self.getInvalidFilenames():
            actionBundle = Mock(spec=ActionBundle)
            actionBundle.name = invalidName
            actionBundle.actions = []
            path = dirPath / f"{invalidName}.json"
            sut = JSONActionBundleDao(str(path))

            # When / Then
            with self.assertRaises(Exception):
                sut.saveAll(data=actionBundle)

    # ---------------------------------------------------------------------
    # JSON DELETE tests
    # ---------------------------------------------------------------------

    def test_delete_shouldDeleteAllContentOfJSONFile(self):
        # Given
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / "Test file to delete.json"
        dataDict = {"key": "value"}

        # Precondition: Test directory for JSON files must be present
        self.assertTrue(path.parent.is_dir(),
                        "Precondition for test: Path to JSON-test-directory must be valid.")

        # Create a fake file
        with open(str(path), 'w', encoding="utf-8") as outfile:
            json.dump(dataDict, outfile)

        # When (this should delete the file's content - not the file itself)
        with JSONActionBundleDao(str(path)) as sut:
            sut.deleteAll()

        # Then
        self.assertEqual(0, os.path.getsize(str(path)),
                         f"Expected file to be empty at path {path} but there is content.")

        # Remove test file
        if path.is_file():
            path.unlink()

    def test_delete_shouldRaiseWhenTryingToDeleteDirectory(self):
        # Given
        path = self.ACTIONBUNDLE_TEST_DIR_PATH

        # Precondition: Test directory for JSON files must be present
        assert path.is_dir()

        # Create one ActionBundle with an ActionBundle.name which for the test becomes a dir name.
        testDirName = "Empty Test Directory"
        # Create a test directory which is expected NOT to be deleted by sut.delete(...)
        path = Path(path, testDirName)
        path.mkdir(exist_ok=True)
        #
        sut = JSONActionBundleDao(str(path))

        # When
        with self.assertRaises(IOError):
            sut.deleteAll()

        # Cleanup: Delete test directory
        if path.exists():
            path.rmdir()

    def test_delete_shouldRaiseIfFileNotFound(self):
        # Given
        path = self.ACTIONBUNDLE_TEST_DIR_PATH / "This test file should not exist.json"
        sut = JSONActionBundleDao(str(path))

        # When
        with self.assertRaises(Exception):
            sut.deleteAll()

    # ---------------------------------------------------------------------
    # JSON INSERT tests
    # ---------------------------------------------------------------------

    def test_insert(self):
        # Given
        stubFile = JSONActionBundleDaoFixture.Filename.GOOGLE_SEARCH.value
        stubPath = Path(self.ACTIONBUNDLE_TEST_DIR_PATH / stubFile)
        testPath = Path(
            self.ACTIONBUNDLE_TEST_DIR_PATH / f"{__class__.__name__}.test_insert.json")

        # Copy a test JSON file with fixed data
        shutil.copy(stubPath, testPath)
        assert testPath.exists()

        # Create some test data to insert
        searchConditions = SearchConditions(strategy=Strategy.BY_XPATH, identifier="Nothing")
        action01 = LoadPageAction(url="https://some.url.com")
        action02 = SendKeysAction(
            searchConditions=searchConditions,
            text="Some test text here."
        )
        actions = [action01, action02]
        actionBundle = ActionBundle(name="A new inserted ActionBundle", actions=actions)

        # Data expressed as expected dict
        expectedDict = {
            "version": 1.0,
            "name": "A new inserted ActionBundle",
            "actions": [
                {
                    "command": 2,
                    "searchStrategy": "",
                    "searchIdentifier": "",
                    "textToSend": "https://some.url.com",
                    "maxWait": 0.0
                },
                {
                    "command": 3,
                    "searchStrategy": "xPath",
                    "searchIdentifier": "Nothing",
                    "textToSend": "Some test text here.",
                    "maxWait": 0.0
                }
            ]
        }

        # When
        with JSONActionBundleDao(str(testPath)) as sut:
            sut.insert(actionBundle)

        # Then
        with open(str(testPath), "r", encoding="utf-8") as file:
            savedData = json.load(file)

        actionBundleTable = savedData.get(JSONActionBundleDao._TABLE_NAME)
        # Expect that there is a root node with key JSONActionBundleDao._TABLE_NAME
        self.assertIsNotNone(actionBundleTable,
                             f"Expected data for table {JSONActionBundleDao._TABLE_NAME}, "
                             f"got None. Table does not seem to exist in data: {savedData}")
        
        # Expect that actionBundleTable is of type list and has 2 entries
        self.assertIsInstance(actionBundleTable, list)
        self.assertEqual(2, len(actionBundleTable))
        # Expect correct values for inserted data
        insertedData = actionBundleTable[1]
        self.assertDictEqual(expectedDict, insertedData)

        # Cleanup
        if testPath.is_file():
            testPath.unlink()

    def test_insert_shouldRaiseOnInvalidDataType(self):
        # Given
        path = Path(
            self.ACTIONBUNDLE_TEST_DIR_PATH / f"{__class__.__name__}.test_insert.json")
        invalidData = Mock(name="Invalid data type")

        with JSONActionBundleDao(str(path)) as sut:
            # When / Then
            with self.assertRaises(TypeError):
                sut.insert(invalidData)

        if path.is_file():
            path.unlink()

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    @staticmethod
    def getInvalidFilenames():
        invalidFilenames = [
            ".Dot as first char is invalid",  # "." as first char is invalid
            "",  # Empty name is invalid
            "FileName/withSlash",  # Slash is invalid
            "\\",  # Backslash is invalid
        ]
        return invalidFilenames
