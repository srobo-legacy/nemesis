import functools
import os
import sys

PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PATH + "/libnemesis/")

import subprocess
import json

import config
import mailer
import helpers
from helpers import log_action

from flask import Flask, request, redirect, url_for
from datetime import timedelta

from libnemesis import User, College, AuthHelper
from sqlitewrapper import PendingEmail, PendingPasswordReset, PendingUser

config.configure_logging()
app = Flask(__name__)

ACTIVATION_DAYS = config.config.getint('nemesis', 'activation_days')
PASSWORD_RESET_DAYS = config.config.getint('nemesis', 'password_reset_days')

PLAINTEXT_HEADER = {'Content-Type': 'text/plain'}

# Note: we don't need to allow form submissions since all our forms
#       are handled by JavaScript attached to the button rather than
#       by traditional submission.
# Note: it's not clear whether or not we need the img-src value:
#       both Firefox 45 and Chrome 49 seem to render the CSS background-images
#       just fine without it, though this seems contrary to the spec.
CSP_VALUE = "connect-src 'self'; " \
          + "img-src 'self'; " \
          + "style-src 'self'; " \
          + "script-src 'self' 'unsafe-eval' ajax.googleapis.com/ajax/libs/; "

CSP_HEADER = {'Content-Security-Policy': CSP_VALUE,
              'X-Content-Security-Policy': CSP_VALUE}

AUTHORIZATION_DENIED = (json.dumps({'authentication_errors':[]}), 403)


def auth_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ah = AuthHelper(request)
        if not ah.auth_will_succeed:
            return ah.auth_error_json, 403

        return func(ah.user, *args, **kwargs)
    return wrapper


@app.route("/")
def index():
    # Work around Flask/Werkzeug bug (https://github.com/pallets/flask/issues/169,
    # https://github.com/pallets/werkzeug/issues/360); fixed in 0.9.8 though we
    # don't have access to that version yet.
    if request.environ['PATH_INFO'] != '/':
        return redirect(url_for('.index'), code=302)

    text = open(PATH + '/templates/index.html').read()
    text = text.replace('$ACTIVATION_DAYS$', str(ACTIVATION_DAYS))
    text = text.replace('$PASSWORD_RESET_DAYS$', str(PASSWORD_RESET_DAYS))
    return text, 200, CSP_HEADER


@app.route("/site/sha")
def sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PATH)


@app.route("/registrations", methods=["POST"])
@auth_required
def register_user(requesting_user):
    if not requesting_user.can_register_users:
        return json.dumps({"error":"YOU_CANT_REGISTER_USERS"}), 403

    teacher_username = requesting_user.username
    college_group    = request.form["college"].strip()
    first_name       = request.form["first_name"].strip()
    last_name        = request.form["last_name"].strip()
    email            = request.form["email"].strip()
    team             = request.form["team"].strip()

    if College(college_group) not in requesting_user.colleges:
        return json.dumps({"error":"BAD_COLLEGE"}), 403

    if team not in [t.name for t in College(college_group).teams]:
        return json.dumps({"error":"BAD_TEAM"}), 403

    if not helpers.is_email_valid(email):
        return json.dumps({"error":"BAD_EMAIL"}), 403

    if not helpers.is_name_valid(first_name):
        return json.dumps({"error":"BAD_FIRST_NAME"}), 403

    if not helpers.is_name_valid(last_name):
        return json.dumps({"error":"BAD_LAST_NAME"}), 403

    if User.name_used(first_name, last_name) or helpers.email_used(email):
        return json.dumps({"error":"DETAILS_ALREADY_USED"}), 403

    u = User.create_new_user(requesting_user, college_group, first_name, last_name)
    verify_code = helpers.create_verify_code(u.username, email)

    pu = PendingUser(u.username)
    pu.teacher_username = teacher_username
    pu.college = college_group
    pu.email = email
    pu.team = team
    pu.verify_code = verify_code
    pu.save()

    log_action('registering user', pu)

    url = url_for('activate_account', username=u.username, code=verify_code, _external=True)
    pu.send_welcome_email(first_name, url)

    rqu_email_vars = { 'name': requesting_user.first_name,
            'activation_days': ACTIVATION_DAYS,
              'pu_first_name': first_name,
               'pu_last_name': last_name,
                'pu_username': pu.username,
                 'pu_college': College(pu.college).name,
                   'pu_email': pu.email,
                    'pu_team': pu.team
                      }
    mailer.email_template(requesting_user.email, 'user_requested', rqu_email_vars)

    return "{}", 202


@app.route("/send-password-reset/<userid>", methods=["POST"])
@auth_required
def send_password_reset(requesting_user, userid):
    user_to_update = User.create_user(userid)
    if not requesting_user.can_administrate(user_to_update):
        return AUTHORIZATION_DENIED

    verify_code = helpers.create_verify_code(user_to_update.username, requesting_user.username)

    ppr = PendingPasswordReset(user_to_update.username)
    ppr.requestor_username = requesting_user.username
    ppr.verify_code = verify_code
    ppr.save()

    log_action('sending password reset', ppr)

    url = url_for('reset_password', username=user_to_update.username, code=verify_code, _external=True)
    ppr.send_reset_email(
        user_to_update.email,
        user_to_update.first_name,
        url,
        "{0} {1}".format(requesting_user.first_name, requesting_user.last_name),
    )

    return "{}", 202


@app.route("/user/<userid>", methods=["GET"])
@auth_required
def user_details(requesting_user, userid):
    if not requesting_user.can_view(userid):
        return AUTHORIZATION_DENIED

    user = User.create_user(userid)
    details = user.details_dictionary_for(requesting_user)

    if 'email' in details:
        # The requesting user can view the emails -- also tell them
        # about any pending changes.
        email_change_rq = PendingEmail(user.username)
        if email_change_rq.in_db:
            new_email = email_change_rq.new_email
            if new_email != details['email']:
                details['new_email'] = new_email
    return json.dumps(details), 200


def request_new_email(user, new_email):
    userid = user.username

    pe = PendingEmail(userid)

    if user.email == new_email:
        if pe.in_db:
            pe.delete()
        return

    verify_code = helpers.create_verify_code(userid, new_email)
    pe.new_email = new_email
    pe.verify_code = verify_code
    pe.save()

    url = url_for('verify_email', username=userid, code=verify_code, _external=True)
    pe.send_verification_email(user.first_name, url)


def notify_ticket_available(user):
    email_vars = { 'first_name': user.first_name }
    mailer.email_template(user.email, 'ticket_available', email_vars)


@app.route("/user/<userid>", methods=["POST"])
@auth_required
def set_user_details(requesting_user, userid):
    user_to_update = User.create_user(userid)
    can_admin = requesting_user.can_administrate(user_to_update)

    if request.form.get("media_consent") == 'true' and requesting_user.can_record_media_consent:
        if not user_to_update.has_media_consent:
            user_to_update.got_media_consent()
            notify_ticket_available(user_to_update)
            user_to_update.save()

        if not can_admin:
            return '{}', 200

    elif not can_admin:
        return AUTHORIZATION_DENIED

    assert can_admin

    user_to_update = User.create_user(userid)
    if request.form.has_key("new_email") and not requesting_user.is_blueshirt:
        new_email = request.form["new_email"]
        request_new_email(user_to_update, new_email)
    # Students aren't allowed to update their own names
    # at this point, if the requesting_user is valid, we know it's a self-edit
    if not requesting_user.is_student:
        fname = request.form.get("new_first_name")
        if fname:
            user_to_update.set_first_name(fname)
        lname = request.form.get("new_last_name")
        if lname:
            user_to_update.set_last_name(lname)
    if request.form.has_key("new_team"):
        team = request.form["new_team"]
        if (not user_to_update.is_blueshirt) and requesting_user.manages_team(team):
            user_to_update.set_team(team)
    if request.form.has_key("new_type") and requesting_user.is_teacher and user_to_update != requesting_user:
        if request.form["new_type"] == 'student':
            user_to_update.make_student()
        elif request.form["new_type"] == 'team-leader':
            user_to_update.make_teacher()
    if request.form.get("withdrawn") == 'true' and not user_to_update.has_withdrawn \
        and requesting_user.can_withdraw(user_to_update):
        user_to_update.withdraw()

    user_to_update.save()

    # Do this separately and last because it makes an immediate change
    # to the underlying database, rather than waiting for save().
    if request.form.has_key("new_password"):
        user_to_update.set_password(request.form["new_password"])

    return '{}', 200


@app.route("/colleges", methods=["GET"])
@auth_required
def colleges(requesting_user):
    if requesting_user.is_blueshirt:
        return json.dumps({"colleges":College.all_college_names()})
    else:
        return AUTHORIZATION_DENIED


@app.route("/colleges/<collegeid>", methods=["GET"])
@auth_required
def college_info(requesting_user, collegeid):
    c = College(collegeid)
    if c in requesting_user.colleges or requesting_user.is_blueshirt:
        response = c.details_dictionary_for(requesting_user)
        return json.dumps(response), 200

    else:
        return AUTHORIZATION_DENIED


@app.route("/activate/<username>/<code>", methods=["GET"])
def activate_account(username, code):
    """
    Verifies to the system that an email address exists, and that the related
    account should be made into a full account.
    Expected to be used only by users clicking links in account-activation emails.
    Not part of the documented API.
    """

    pu = PendingUser(username)

    if not pu.in_db:
        return "No such user account", 404, PLAINTEXT_HEADER

    if pu.age > timedelta(days = ACTIVATION_DAYS):
        return "Request not valid", 410, PLAINTEXT_HEADER

    if pu.verify_code != code:
        return "Invalid verification code", 403, PLAINTEXT_HEADER

    log_action('activating user', pu)

    from libnemesis import srusers
    new_pass = srusers.users.GenPasswd()

    u = User(username)
    u.set_email(pu.email)
    u.set_team(pu.team)
    u.set_college(pu.college)
    u.set_password(new_pass)
    u.make_student()
    u.save()

    # confirm the details to the competitor
    email_vars = {
        'username': username,
           'email': u.email,
      'first_name': u.first_name,
       'last_name': u.last_name
    }
    mailer.email_template(u.email, 'user_activated', email_vars)

    # let the team-leader know
    rq_user = User.create_user(pu.teacher_username)
    email_vars = { 'name': rq_user.first_name,
            'au_username': username,
          'au_first_name': u.first_name,
           'au_last_name': u.last_name
                 }
    mailer.email_template(rq_user.email, 'user_activated_team_leader', email_vars)

    pu.delete()

    html = open(PATH + "/templates/activate.html").read()
    replacements = { 'first_name': u.first_name
                   ,  'last_name': u.last_name
                   ,   'password': new_pass
                   ,      'email': u.email
                   ,   'username': username
                   ,       'root': url_for('.index')
                   }

    html = html.format(**replacements)

    return html, 200, CSP_HEADER



@app.route("/reset_password/<username>/<code>", methods=["GET"])
def reset_password(username, code):
    """
    Resets a user's password after they've clicked a link in an email we
    sent them, then serves up a page for them to change their password.
    Not part of the documented API.
    """

    ppr = PendingPasswordReset(username)

    if not ppr.in_db:
        return "No such user account", 404, PLAINTEXT_HEADER

    if ppr.age > timedelta(days = PASSWORD_RESET_DAYS):
        return "Request not valid", 410, PLAINTEXT_HEADER

    if ppr.verify_code != code:
        return "Invalid verification code", 403, PLAINTEXT_HEADER

    log_action('resetting user password', ppr)

    from libnemesis import srusers
    new_pass = srusers.users.GenPasswd()

    u = User(username)
    u.set_password(new_pass)
    # No need to save since set_password happens immediately

    ppr.delete()

    html = open(PATH + "/templates/password_reset.html").read()
    replacements = { 'first_name': u.first_name
                   ,  'last_name': u.last_name
                   ,   'password': new_pass
                   ,   'username': username
                   ,       'root': url_for('.index')
                   }

    html = html.format(**replacements)

    return html, 200, CSP_HEADER


@app.route("/verify/<username>/<code>", methods=["GET"])
def verify_email(username, code):
    """
    Verifies to the system that an email address exists, and assigns it to a user.
    Expected to be used only by users clicking links in email-verfication emails.
    Not part of the documented API.
    """

    change_request = PendingEmail(username)

    if not change_request.in_db:
        return "No such change request", 404, PLAINTEXT_HEADER

    email_change_days = config.config.getint('nemesis', 'email_change_days')
    max_age = timedelta(days = email_change_days)

    if change_request.age > max_age:
        return "Request not valid", 410, PLAINTEXT_HEADER

    if change_request.verify_code != code:
        return "Invalid verification code", 403, PLAINTEXT_HEADER

    log_action('changing email', user = username, new_email = change_request.new_email)

    u = User(change_request.username)
    u.set_email(change_request.new_email)
    u.save()

    return "Email address successfully changed", 200, PLAINTEXT_HEADER


if __name__ == "__main__":
    # Run the app in debug mode
    app.debug = True
    app.run(host='0.0.0.0')
