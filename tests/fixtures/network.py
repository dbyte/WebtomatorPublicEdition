# fixtures.network.py
from pathlib import Path

__MY_ROOT = Path(__file__).parent

TEST_USERDATA_DIR_PATH = Path(__MY_ROOT, "../resources/userdata")
assert TEST_USERDATA_DIR_PATH.is_dir()

# ----------------------------------------------------------------------------------
# Web proxy fixtures
# ----------------------------------------------------------------------------------

assert Path(TEST_USERDATA_DIR_PATH, "proxies").is_dir()

TEST_TEMP_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/temp_proxies.txt")

TEST_0VALID_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_0valid.txt")

TEST_6VALID_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_6valid.txt")

TEST_EXACT3_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_exact3.txt")

TEST_5WITH2DUPLICATES_PROXIES_REPO_PATH = \
    Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_5with2Duplicates.txt")

TEST_EMPTYFILE_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_emptyFile.txt")

TEST_INVALID_FILESUFFIX_PROXIES_REPO_PATH = \
    Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_invalidFileSuffix.tttxttt")

TEST_INTEGRATION_PROXIES_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "proxies/proxies_gitignore.txt")
TEST_INTEGRATION_PROXIES_REPO_PATH.touch()  # create file if not exists

# ----------------------------------------------------------------------------------
# User agent fixtures
# ----------------------------------------------------------------------------------

assert Path(TEST_USERDATA_DIR_PATH, "useragents").is_dir()

TEST_USERAGENTS_TEMP_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "useragents/temp_useragents.txt")

TEST_USERAGENTS_0VALID_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "useragents/UserAgents_0valid.txt")

TEST_USERAGENTS_3VALID_REPO_PATH = Path(TEST_USERDATA_DIR_PATH, "useragents/UserAgents_3valid.txt")

TEST_USERAGENTS_INTEGRATION_REPO_PATH = \
    Path(TEST_USERDATA_DIR_PATH, "useragents/UserAgents_IntegrationTest.txt")
TEST_USERAGENTS_INTEGRATION_REPO_PATH.touch()  # create file if not exists

# ----------------------------------------------------------------------------------
# Messengers fixtures
# ----------------------------------------------------------------------------------

TEST_MESSENGERS_DIR_PATH = Path(TEST_USERDATA_DIR_PATH, "messengers")
assert TEST_MESSENGERS_DIR_PATH.is_dir()

# Main repository
TEST_MESSENGERS_INTEGRATION_REPO_PATH = \
    Path(TEST_MESSENGERS_DIR_PATH, "Messengers_gitignore.json")
TEST_MESSENGERS_INTEGRATION_REPO_PATH.touch()  # create file if not exists

# Just an alternate repository with different endpoints / IDs / tokens
TEST_MESSENGERS_INTEGRATION_REPO_PATH2 = \
    Path(TEST_MESSENGERS_DIR_PATH, "Messengers2_gitignore.json")