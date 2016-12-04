
import datetime
import re
import sys
import unittest

import test_helpers

sys.path.append("../../nemesis")
from sqlitewrapper import PendingPasswordReset, sqlite_connect
from config import config

sys.path.append("../../nemesis/libnemesis")
from libnemesis import User


def setup_password_reset(for_user, verify_code):
    ppr = PendingPasswordReset(for_user)
    ppr.requestor_username = 'blueshirt'
    ppr.verify_code = verify_code
    ppr.save()

class SendPasswordResetTests(unittest.TestCase):
    longMessage = True

    def setUp(self):
        test_helpers.delete_db()

    def tearDown(self):
        test_helpers.delete_db()

    def test_post_no_user(self):
        r, data = test_helpers.server_post("/send-password-reset/student_coll1_1")
        self.assertEqual(403, r.status, data)

    def test_post_by_blueshirt(self):
        params = {"username":"blueshirt",
                  "password":"blueshirt"}

        r, data = test_helpers.server_post("/send-password-reset/student_coll1_1", params)

        self.assertEqual(202, r.status, data)

        user = User('student_coll1_1')

        ps = test_helpers.last_email()
        toaddr = ps.toaddr
        self.assertEqual(user.email, toaddr)

        vars = ps.template_vars
        self.assertEqual(user.first_name, vars['name'], "Wrong first name")
        self.assertEqual('Blue Shirt', vars['requestor_name'], "Wrong requestor name")

        template = ps.template_name
        self.assertEqual('password_reset', template, "Wrong email template")

        test_helpers.assert_load_template(template, vars)

        ppr = PendingPasswordReset('student_coll1_1')
        self.assertTrue(ppr.in_db, "{0} should been in the database.".format(ppr))
        self.assertEqual('blueshirt', ppr.requestor_username, "Wrong requestor username.")

        self.assertIn(ppr.verify_code, vars['password_reset_url'], "Wrong verify code")

    def test_verify_needs_request(self):
        r, data = test_helpers.server_get("/reset_password/nope/bees")
        self.assertEqual(404, r.status, data)

    def test_verify_wrong_code(self):
        setup_password_reset('abc', 'wrong')

        r, data = test_helpers.server_get("/reset_password/abc/bees")
        self.assertEqual(403, r.status, data)

    def test_verify_outdated_request(self):
        with sqlite_connect() as conn:
            cur = conn.cursor()
            statement = "INSERT INTO password_resets (username, requestor_username, request_time, verify_code) VALUES (?,?,?, ?)"
            days = config.getint('nemesis', 'password_reset_days')
            old = datetime.datetime.now() - datetime.timedelta(days = days + 2)
            arguments = ('abc', 'blueshirt', old.strftime('%Y-%m-%d %H:%M:%S'), 'bees')
            cur.execute(statement, arguments)
            conn.commit()

        r, data = test_helpers.server_get("/reset_password/abc/bees")
        self.assertEqual(410, r.status, data)

    def test_verify_success(self):
        username = "student_coll1_1"
        setup_password_reset(username, 'bees')

        r, data = test_helpers.server_get("/reset_password/" + username + "/bees")
        self.assertEqual(200, r.status, data)

        try:
            match = re.search(r'"password": "([^"]+)"', data)
            self.assertTrue(match, "Failed to extract password")

            new_password = match.group(1)

            user = User.create_user(username, new_password)
            self.assertTrue(user.is_authenticated, "Wrong password ({0}) found in page!".format(new_password))
        finally:
            User(username).set_password('cows')
