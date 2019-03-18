
from datetime import timedelta
from nose.tools import raises, with_setup

import test_helpers

from sqlitewrapper import PendingPasswordReset


@with_setup(test_helpers.delete_db)
def test_none_listed_at_start():
    all_list = PendingPasswordReset.ListAll()
    assert len(all_list) == 0

@with_setup(test_helpers.delete_db)
def test_one_listed():
    test_creation()

    all_list = PendingPasswordReset.ListAll()
    assert len(all_list) == 1

    ppr = all_list[0]

    assert type(ppr) == PendingPasswordReset

    assert ppr.in_db
    assert ppr.username == 'abc'
    assert ppr.requestor_username == 'dave'
    assert ppr.verify_code == 'bibble'

@with_setup(test_helpers.delete_db)
def test_none_listed_after_removal():
    test_creation()

    all_list = PendingPasswordReset.ListAll()
    for ppr in all_list:
        ppr.delete()

    all_list = PendingPasswordReset.ListAll()
    assert len(all_list) == 0

@with_setup(test_helpers.delete_db)
def test_empty_at_start():
    ppr = PendingPasswordReset('abc')
    assert ppr.in_db == False
    assert ppr.requestor_username is None
    assert ppr.verify_code is None
    assert ppr.age == timedelta()

def test_properties():
    ppr = PendingPasswordReset('abc')
    ppr.requestor_username = 'dave'
    ppr.verify_code = 'bibble'

    assert ppr.username == 'abc'
    assert ppr.requestor_username == 'dave'
    assert ppr.verify_code == 'bibble'

@with_setup(test_helpers.delete_db, test_helpers.delete_db)
def test_creation():
    ppr = PendingPasswordReset('abc')
    ppr.requestor_username = 'dave'
    ppr.verify_code = 'bibble'

    ppr.save()
    assert ppr.in_db

    ppr = PendingPasswordReset('abc')
    assert ppr.in_db
    assert ppr.username == 'abc'
    assert ppr.requestor_username == 'dave'
    assert ppr.verify_code == 'bibble'
    age = ppr.age
    assert age > timedelta()
    assert age < timedelta(minutes = 1)

@with_setup(test_helpers.delete_db, test_helpers.delete_db)
def test_delete():
    test_creation()

    ppr = PendingPasswordReset('abc')
    ppr.delete()
    assert not ppr.in_db

    ppr = PendingPasswordReset('abc')
    assert not ppr.in_db

@with_setup(test_helpers.delete_db, test_helpers.delete_db)
def test_send_email():
    first_name = 'jim'
    verification_url = 'https://verify'
    email = 'email@example.com'
    requestor_name = 'Dave Smith'

    ppr = PendingPasswordReset('abc')
    ppr.requestor_username = 'dave'
    ppr.send_reset_email(email, first_name, verification_url, requestor_name)

    ps = test_helpers.last_email()

    vars = ps.template_vars
    assert first_name == vars['name']
    assert verification_url == vars['password_reset_url']
    assert requestor_name == vars['requestor_name']
    toaddr = ps.toaddr
    assert email == toaddr

    template = ps.template_name
    assert template == 'password_reset'

    test_helpers.assert_load_template(template, vars)

@raises(AttributeError)
def test_invalid_property():
    ppr = PendingPasswordReset('abc')
    print ppr.bacon
