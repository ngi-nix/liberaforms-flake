"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast
import pytest
from urllib.parse import urlparse
from liberaforms.models.user import User
from liberaforms.utils import validators

from tests.unit.conftest import dummy_user

#@pytest.mark.usefixtures('users')
#@pytest.mark.order(after="TestAdmin")
class TestUser():

    def test_save_new_user(self, db, dummy_user, users):
        dummy_user.save()
        users['test_user']=dummy_user
        assert users['test_user'].id != None

    def test_login(self, client, users):
        """ Tests bad credentials and good credentials """
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['test_user'].username,
                            "password": os.environ['TEST_USER_PASSWORD']+'*',
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<form action="/user/login"' in html
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['test_user'].username,
                            "password": os.environ['TEST_USER_PASSWORD'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_change_language(self, users, client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
        """
        #with caplog.at_level(logging.WARNING, logger="app.access"):
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        "/user/change-language",
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].preferences['language'] != unavailable_language
        available_language = 'ca'
        response = client.post(
                        "/user/change-language",
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].preferences['language'] == available_language
        users['test_user'].save()

    def test_change_password(self, users, client):
        """ Tests bad password and good password
            as defined in ./liberaforms/utils/validators.py
        """
        password_hash = users['test_user'].password_hash
        bad_password="1234"
        response = client.post(
                        "/user/reset-password",
                        data = {
                            "password": bad_password,
                            "password2": bad_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].password_hash == password_hash
        valid_password="this is a valid password"
        response = client.post(
                        "/user/reset-password",
                        data = {
                            "password": valid_password,
                            "password2": valid_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert users['test_user'].password_hash != password_hash
        # reset the password to the value defined in ./tests/test.env. Required by other tests
        password_hash = validators.hash_password(os.environ['TEST_USER_PASSWORD'])
        users['test_user'].password_hash = password_hash
        users['test_user'].save()

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_change_email(self, client):
        """ Not impletmented """
        pass

    def test_toggle_new_answer_notification(self, users, client):
        current_default = users['test_user'].preferences["newEntryNotification"]
        response = client.post(
                        "/user/toggle-new-entry-notification",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert response.is_json == True
        assert users['test_user'].preferences["newEntryNotification"] != current_default

    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div id="blurb" class="marked-up">' in html
        assert '<a class="nav-link" href="/user/login">' in html
