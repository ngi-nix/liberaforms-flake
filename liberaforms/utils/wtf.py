"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2020 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import re
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, PasswordField, BooleanField, RadioField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask import g
from flask_babel import lazy_gettext as _

from liberaforms import app
from liberaforms.models.user import User
from liberaforms.utils.sanitizers import sanitize_username
from liberaforms.utils import validators


class NewUser(FlaskForm):
    username = StringField(_("Username"), validators=[DataRequired()])
    email = StringField(_("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password again"), validators=[DataRequired(), EqualTo('password')])
    termsAndConditions = BooleanField()
    DPLConsent = BooleanField()

    def validate_username(self, username):
        if username.data != sanitize_username(username.data):
            raise ValidationError(_("Username is not valid"))
            return False
        if username.data in app.config['RESERVED_USERNAMES']:
            raise ValidationError(_("Please use a different username"))
            return False
        if User.find(username=username.data):
            raise ValidationError(_("Please use a different username"))

    def validate_email(self, email):
        if User.find(email=email.data) or email.data in app.config['ROOT_USERS']:
            raise ValidationError(_("Please use a different email address"))

    def validate_password(self, password):
        if validators.pwd_policy.test(password.data):
            raise ValidationError(_("Your password is weak"))

    def validate_termsAndConditions(self, termsAndConditions):
        if g.site.terms_consent_id in g.site.newUserConsentment and not termsAndConditions.data:
            raise ValidationError(_("Please accept our terms and conditions"))

    def validate_DPLConsent(self, DPLConsent):
        if g.site.DPL_consent_id in g.site.newUserConsentment and not DPLConsent.data:
            raise ValidationError(_("Please accept our data protection policy"))


class Login(FlaskForm):
    username = StringField(_("Username"), validators=[DataRequired()])
    password = PasswordField(_("Password"), validators=[DataRequired()])

    def validate_username(self, username):
        if username.data != sanitize_username(username.data):
            return False


class DeleteAccount(FlaskForm):
    delete_username = StringField(_("Your username"), validators=[DataRequired()])
    delete_password = PasswordField(_("Your password"), validators=[DataRequired()])

    def validate_delete_username(self, delete_username):
        if delete_username.data != g.current_user.username:
            raise ValidationError(_("That is not your username"))
            return False

    def validate_delete_password(self, delete_password):
        if not validators.verify_password(delete_password.data, g.current_user.password_hash):
            raise ValidationError(_("That is not your password"))


class GetEmail(FlaskForm):
    email = StringField(_("Email address"), validators=[DataRequired(), Email()])


class ChangeEmail(FlaskForm):
    email = StringField(_("New email address"), validators=[DataRequired(), Email()])

    def validate_email(self, email):
        if User.find(email=email.data) or email.data in app.config['ROOT_USERS']:
            raise ValidationError(_("Please use a different email address"))

class ResetPassword(FlaskForm):
    password = PasswordField(_("Password"), validators=[DataRequired()])
    password2 = PasswordField(_("Password again"), validators=[DataRequired(), EqualTo('password')])

    def validate_password(self, password):
        if validators.pwd_policy.test(password.data):
            raise ValidationError(_("Your password is weak"))


class smtpConfig(FlaskForm):
    host = StringField(_("Email server"), validators=[DataRequired()])
    port = IntegerField(_("Port"))
    encryption = SelectField(_("Encryption"), choices=[ ('None', 'None'),
                                                        ('SSL', 'SSL'),
                                                        ('STARTTLS', 'STARTTLS (maybe)')])
    user = StringField(_("User"))
    password = StringField(_("Password"))
    noreplyAddress = StringField(_("Sender address"), validators=[DataRequired(), Email()])


class NewInvite(FlaskForm):
    email = StringField(_("New user's email"), validators=[DataRequired(), Email()])
    message = TextAreaField(_("Include message"), validators=[DataRequired()])
    admin = BooleanField(_("Make the new user an Admin"))

    def validate_email(self, email):
        if User.find(email=email.data) or email.data in app.config['ROOT_USERS']:
            raise ValidationError(_("Please use a different email address"))


class ChangeMenuColor(FlaskForm):
    hex_color = StringField(_("HTML color code"), validators=[DataRequired()])
    def validate_hex_color(self, hex_color):
        if not validators.is_hex_color(hex_color.data):
            raise ValidationError(_("Not a valid HTML color code"))
