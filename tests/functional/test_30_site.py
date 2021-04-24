"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from io import BytesIO
import pathlib

class TestSiteConfig():

    def test_login_admin(cls, users, client):
        response = client.post(
                        "/user/login",
                        data = {
                            "username": users['admin'].username,
                            "password": users["admin_password"],
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert "<!-- my_forms_page -->" in html
        assert '<a class="nav-link" href="/user/logout">' in html

    def test_change_sitename(cls, site, client):
        sitename = site.siteName
        new_name = "New name!!"
        response = client.post(
                        "/site/change-sitename",
                        data = {
                            "sitename": new_name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.siteName != sitename

    def test_change_default_language(cls, site, client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
        """
        language = site.defaultLanguage
        unavailable_language = 'af' # Afrikaans
        response = client.post(
                        "/site/change-default-language",
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == language
        available_language = 'ca'
        response = client.post(
                        "/site/change-default-language",
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage != language

    def test_toggle_invitation_only(cls, site, client):
        invitation_only = site.invitationOnly
        response = client.post(
                        "/site/toggle-invitation-only",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.invitationOnly != invitation_only

    @pytest.mark.skip(reason="TODO")
    def test_set_consent_texts(cls, client):
        pass

    def test_change_menucolor(cls, site, client):
        """ Tests valid and invalid html hex color
        """
        color = site.menuColor
        bad_color = "green"
        response = client.post(
                        "/site/change-menu-color",
                        data = {
                            "hex_color": bad_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor == color
        good_color = "#cccccc"
        response = client.post(
                        "/site/change-menu-color",
                        data = {
                            "hex_color": good_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor != color

    def test_change_favicon(self, app, client):
        """ Tests valid and invalid image files in ./tests/assets
        """
        favicon_path = f"{app.config['BRAND_DIR']}/favicon.png"
        initial_favicon_stats = os.stat(favicon_path)
        invalid_favicon = "favicon_invalid.jpeg"
        with open(f'./assets/{invalid_favicon}', 'rb') as f:
            stream = BytesIO(f.read())
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=invalid_favicon,
            content_type="image/png",
        )
        response = client.post(
                    '/site/change-icon',
                    data = {
                        'file': file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size == os.stat(favicon_path).st_size

        valid_favicon = "favicon_valid.png"
        with open(f'./assets/{valid_favicon}', 'rb') as f:
            stream = BytesIO(f.read())
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_favicon,
            content_type="image/png",
        )
        response = client.post(
                    '/site/change-icon',
                    data = {
                        'file': file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size

    def test_restore_default_favicon(self, app, client):
        favicon_path = f"{app.config['BRAND_DIR']}/favicon.png"
        initial_favicon_stats = os.stat(favicon_path)
        response = client.get(
                        "/site/reset-favicon",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size

    def test_edit_public_link_creation(self, site, client):
        """ Tests valid and invalid ports
        """
        response = client.get(
                        "/site/edit",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<span id="site_scheme">' in html
        # toggle site_scheme
        initial_scheme = site.scheme
        response = client.post(
                    '/site/toggle-scheme',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.scheme != initial_scheme
        # change port
        initial_port = site.port
        invalid_port = "i_am_a_string"
        response = client.post(
                    f'/site/change-port/{invalid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 400
        assert site.port == initial_port
        valid_port = 5555
        response = client.post(
                    f'/site/change-port/{valid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.port != initial_port

    def test_edit_landing_page(self, site, client):
        response = client.post(
                    '/site/save-blurb',
                    data = {
                        'editor': "# Tested !!",
                    },
                    follow_redirects=True,
                )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<h1>Tested !!</h1>' in html
