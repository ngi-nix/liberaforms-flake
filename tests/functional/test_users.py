"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import ast
from urllib.parse import urlparse
import pytest #, logging
from liberaforms.models.user import User


#@pytest.mark.usefixtures('dummy_user')
@pytest.mark.order(after="TestAdmin")
class TestUser():

    def test_dummy_user(self, dummy_user):
        assert dummy_user.id != None

    def test_login(self, client, dummy_user):
        """ Tests bad credentials and good credentials """
        response = client.post(
                        "/user/login",
                        data = {
                            "username": os.environ['TEST_USERNAME'],
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
                            "username": dummy_user.username,
                            "password": os.environ['TEST_USER_PASSWORD'],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_change_language(self, dummy_user, client):
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
        assert dummy_user.preferences['language'] != unavailable_language

        available_language = 'ca'
        response = client.post(
                        "/user/change-language",
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_user.preferences['language'] == available_language
        dummy_user.save()

    def test_change_password(self, dummy_user, client):
        """ Tests bad password and good password
            as defined in ./liberaforms/utils/validators.py
        """
        password_hash = dummy_user.password_hash
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
        assert dummy_user.password_hash == password_hash
        good_password="this is a good password"
        response = client.post(
                        "/user/reset-password",
                        data = {
                            "password": good_password,
                            "password2": good_password
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_user.password_hash != password_hash

    @pytest.mark.skip(reason="No way of currently testing this")
    def test_change_email(self, client):
        """ Not impletmented """
        pass

    def test_new_answer_default_notification(self, dummy_user, client):
        current_default = dummy_user.preferences["newEntryNotification"]
        response = client.post(
                        "/user/toggle-new-entry-notification",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert dummy_user.preferences["newEntryNotification"] != current_default


class TestAdmin:

    def test_bootstrap_first_admin(self, db, client):
        """ Creates a new admin user using ROOT_USER
            as defined in ./tests/test.env
        """
        root_user_email = ast.literal_eval(os.environ['ROOT_USERS'])[0]
        response = client.post(
                        "/site/recover-password",
                        data = {
                            "email": root_user_email,
                        },
                        follow_redirects=False,
                    )
        assert response.status_code == 302
        # this path contains the invite token
        new_user_url = urlparse(response.location).path
        username = root_user_email.split('@')[0]
        password = "a good password"
        response = client.post(
                        new_user_url,
                        data = {
                            "username": username,
                            "email": root_user_email,
                            "password": password,
                            "password2": password,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- my_forms_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html
        user = User.find(username=username)
        assert user.admin['isAdmin'] == True


    def test_logout(self, client):
        response = client.post(
                        "/user/logout",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<a class="nav-link" href="/user/login">' in html