
import os
import sys

sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common_test_helpers import delete_db, last_email, assert_load_template, template
