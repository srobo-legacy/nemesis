
from datetime import timedelta
import hashlib
import logging
import random
import re
import os
import sys
from unidecode import unidecode

from config import config
import mailer
from sqlitewrapper import PendingEmail, PendingSend, PendingUser

PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, PATH + '/libnemesis/')

from libnemesis import srusers, User

def log_action(action, *args, **kwargs):
    keyed = [k + ": " + str(v) for k, v in kwargs.iteritems()]
    details = ", ".join(map(str, args) + keyed)
    logging.info("{0}: {1}".format(action, details))

def is_email_valid(email):
    return re.match('.+@.+\...+', email)

def is_name_valid(name):
    if len(name) == 0:
        return False
    first = unidecode(name[0])[0]
    return first.isalpha()

def ensure_str(string):
    if isinstance(string, unicode):
        return string.encode('utf-8')
    return string

def create_verify_code(username, new_email):
    """
    An increadibly weak way of generating a 'random' looking string which
    we can use to verify the authenticity of an email address.
    The aim here is mostly to check that it exists, so absolute security
    isn't strictly needed. The overall length is 160 characters.
    """
    combined = ensure_str(username) + ensure_str(new_email)
    user_part = hashlib.md5(combined).hexdigest()
    random_part = hex(random.getrandbits(128))[2:-1]
    code = random_part + user_part
    return code

def email_used(email):
    if User.email_used(email):
        return True

    if any(pe.new_email == email for pe in PendingEmail.ListAll()):
        return True

    if any(pu.email == email for pu in PendingUser.ListAll()):
        return True

    return False

## Helpers created for tidying things up, mainly for use in cron

def clear_old_emails():
    # deliberately a larger delta than we restrict against to avoid
    # accidentally removing vaild entries
    email_change_days = config.getint('nemesis', 'email_change_days')
    email_change_days += 0.5
    max_age = timedelta(days = email_change_days)

    for pe in PendingEmail.ListAll():
        if pe.age > max_age:
            log_action('expiring email change', pe)
            pe.delete()

def inform_competitor_registration_expired(user_email, expired_user):

    email_vars = { 'name': expired_user.first_name }

    mailer.email_template(user_email, 'registration_expired', email_vars)

def inform_team_lead_registration_expired(team_leader, expired_user):

    email_vars = { 'name': team_leader.first_name,
          'pu_first_name': expired_user.first_name,
           'pu_last_name': expired_user.last_name
                 }

    mailer.email_template(team_leader.email, 'registration_expired_team_leader', email_vars)

def clear_old_registrations():
    # deliberately a larger delta than we restrict against to avoid
    # accidentally removing vaild entries
    activation_days = config.getint('nemesis', 'activation_days')
    activation_days += 0.5
    max_age = timedelta(days = activation_days)

    for pu in PendingUser.ListAll():
        if pu.age > max_age:
            log_action('expiring registration', pu)
            pu.delete()
            expired = User(pu.username)
            expired.delete()

            inform_competitor_registration_expired(pu.email, expired)
            team_leader = User(pu.teacher_username)
            inform_team_lead_registration_expired(team_leader, expired)

def send_emails(limit = 50):
    unsent_mails = PendingSend.Unsent(max_results = limit)
    for ps in unsent_mails:
        mailer.try_send(ps)
