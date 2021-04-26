# fixtures.scraper.py
from pathlib import Path

__MY_ROOT = Path(__file__).parent

# ----------------------------------------------------------------------------------
# Scraper configuration fixtures
# ----------------------------------------------------------------------------------

TEST_CONFIGURATIONS_DIR_PATH = Path(__MY_ROOT, "../resources/userdata/configurations")
assert TEST_CONFIGURATIONS_DIR_PATH.is_dir()

TEST_VALID_CONFIGURATION_PATH = Path(
    TEST_CONFIGURATIONS_DIR_PATH, "Config_Valid.json")

TEST_EMPTY_DATABASE_CONFIGURATION_PATH = Path(
    TEST_CONFIGURATIONS_DIR_PATH, "Config_EmptyDatabase.json")

# ----------------------------------------------------------------------------------
# Shop response fixtures
# ----------------------------------------------------------------------------------

TEST_RESPONSE_DIR_PATH = Path(__MY_ROOT, "../resources/responseFixtures")
assert TEST_RESPONSE_DIR_PATH.is_dir()

TEST_SHOP_RESPONSE_DIR_PATH = Path(TEST_RESPONSE_DIR_PATH, "shopResponse")
assert TEST_SHOP_RESPONSE_DIR_PATH.is_dir()

TEST_FOOTDISTRICT_SHOP_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Footdistrict_ShopResponse.html")

TEST_FOOTDISTRICT_PRODUCT_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Footdistrict_ProductResponse.html")

TEST_SOLEBOX_SHOP_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Solebox_ShopResponse.html")

TEST_SOLEBOX_PRODUCT_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Solebox_ProductResponse.html")

TEST_BSTN_SHOP_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "BSTN_ShopResponse.html")

TEST_BSTN_PRODUCT_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "BSTN_ProductResponse.html")

TEST_SNEAKAVENUE_SHOP_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Sneakavenue_ShopResponse.html")

TEST_SNEAKAVENUE_PRODUCT_HTML_RESPONSE = Path(
    TEST_SHOP_RESPONSE_DIR_PATH, "Sneakavenue_ProductResponse.html")