"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
import werkzeug
from io import BytesIO

class TestSiteConfig():
    def test_change_sitename(cls, site, admin_client, anon_client):
        url = "/site/change-sitename"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' not in html
        initial_sitename = site.siteName
        new_name = "New name!!"
        response = admin_client.post(
                        "/site/change-sitename",
                        data = {
                            "sitename": new_name,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.siteName != initial_sitename

    def test_change_default_language(cls, site, admin_client, anon_client):
        """ Tests unavailable language and available language
            as defined in ./liberaforms/config.py
            Tests admin permission
        """
        url = "/site/change-default-language"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        initial_language = site.defaultLanguage
        response = admin_client.get(
                        url,
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<!-- change_language_page -->' in html
        unavailable_language = 'af' # Afrikaans
        response = admin_client.post(
                        url,
                        data = {
                            "language": unavailable_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == initial_language
        available_language = 'ca'
        response = admin_client.post(
                        url,
                        data = {
                            "language": available_language
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.defaultLanguage == available_language

    def test_toggle_invitation_only(cls, site, admin_client, anon_client):
        url = "/site/toggle-invitation-only"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        invitation_only = site.invitationOnly
        response = admin_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.invitationOnly != invitation_only

    @pytest.mark.skip(reason="TODO")
    def test_set_consent_texts(cls, admin_client):
        pass

    def test_change_menucolor(cls, site, admin_client, anon_client):
        """ Tests valid and invalid html hex color
            Tests admin permission
        """
        url = "/site/change-menu-color"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        url,
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<div class="menu-color-options">' in html
        initial_color = site.menuColor
        bad_color = "green"
        response = admin_client.post(
                        url,
                        data = {
                            "hex_color": bad_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor == initial_color
        html = response.data.decode()
        assert '<div class="menu-color-options">' in html
        valid_color = "#cccccc"
        response = admin_client.post(
                        url,
                        data = {
                            "hex_color": valid_color
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.menuColor != initial_color
        html = response.data.decode()
        assert '<div id="site_settings"' in html

    def test_change_favicon(self, app, admin_client, anon_client):
        """ Tests valid and invalid image files in ./tests/assets
            Tests admin permission
        """
        url = "/site/change-icon"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                    url,
                    follow_redirects=False,
                )
        html = response.data.decode()
        assert '<form method="POST" enctype=multipart/form-data >' in html
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
        response = admin_client.post(
                    url,
                    data = {
                        'file': file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size == os.stat(favicon_path).st_size
        html = response.data.decode()
        assert '<form method="POST" enctype=multipart/form-data >' in html
        valid_favicon = "favicon_valid.png"
        with open(f'./assets/{valid_favicon}', 'rb') as f:
            stream = BytesIO(f.read())
        file = werkzeug.datastructures.FileStorage(
            stream=stream,
            filename=valid_favicon,
            content_type="image/png",
        )
        response = admin_client.post(
                    url,
                    data = {
                        'file': file,
                    },
                    follow_redirects=True,
                    content_type='multipart/form-data',
                )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size
        html = response.data.decode()
        assert '<div id="site_settings"' in html

    def test_restore_default_favicon(self, app, admin_client, anon_client):
        url = "/site/reset-favicon"
        response = anon_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        favicon_path = f"{app.config['BRAND_DIR']}/favicon.png"
        initial_favicon_stats = os.stat(favicon_path)
        response = admin_client.get(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert initial_favicon_stats.st_size != os.stat(favicon_path).st_size
        html = response.data.decode()
        assert '<div id="site_settings"' in html

    def test_edit_public_link_creation(self, site, admin_client, anon_client):
        """ Tests valid and invalid ports
            Tests admin permission
        """
        response = anon_client.get(
                        "/site/edit",
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.get(
                        "/site/edit",
                        follow_redirects=False,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<span id="site_scheme">' in html
        # toggle site_scheme
        initial_scheme = site.scheme
        response = admin_client.post(
                    '/site/toggle-scheme',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.scheme != initial_scheme
        # change port
        initial_port = site.port
        invalid_port = "i_am_a_string"
        response = admin_client.post(
                    f'/site/change-port/{invalid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 400
        assert site.port == initial_port
        valid_port = 5555
        response = admin_client.post(
                    f'/site/change-port/{valid_port}',
                    follow_redirects=True,
                )
        assert response.status_code == 200
        assert site.port != initial_port

    def test_edit_landing_page(self, site, admin_client, anon_client):
        """ Posts markdown and tests resulting HTML
            Tests admin permission
        """
        url = "/site/save-blurb"
        response = anon_client.post(
                        url,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        response = admin_client.post(
                    url,
                    data = {
                        'editor': "# Tested !!\nline1\nline2",
                    },
                    follow_redirects=True,
                )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<h1>Tested !!</h1>' in html
        assert '<p>line1<br />\nline2</p>' in html

    def test_save_smtp_config(self, site, admin_client):
        """ Tests invalid and valid smtp configuration
            Tests admin permission
        """
        initial_smtp_config = site.smtpConfig
        response = admin_client.get(
                        "/site/email/config",
                        follow_redirects=False,
                    )
        html = response.data.decode()
        assert '<form method="POST" action="/site/email/config">' in html
        invalid_smtp_conf = {
            'host': 'smtp.example.com',
            'port': "i_am_a_string",
            'encryption': 'SSL',
            'user': 'username',
            'password': 'password',
            'noreplyAddress': 'noreply@example.com'
        }
        response = admin_client.post(
                        "/site/email/config",
                        data = invalid_smtp_conf,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.smtpConfig == initial_smtp_config
        html = response.data.decode()
        assert '<form method="POST" action="/site/email/config">' in html
        valid_smtp_conf = {
            'host': os.environ['TEST_SMTP_HOST'],
            'port': int(os.environ['TEST_SMTP_PORT']),
            'encryption': os.environ['TEST_SMTP_ENCRYPTION'],
            'user': os.environ['TEST_SMTP_USERNAME'],
            'password': os.environ['TEST_SMTP_USER_PASSWORD'],
            'noreplyAddress': os.environ['TEST_SMTP_NO_REPLY']
        }
        response = admin_client.post(
                        "/site/email/config",
                        data = valid_smtp_conf,
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        assert site.smtpConfig['host'] == os.environ['TEST_SMTP_HOST']
        assert site.smtpConfig['port'] == int(os.environ['TEST_SMTP_PORT'])
        assert site.smtpConfig['encryption'] == os.environ['TEST_SMTP_ENCRYPTION']
        assert site.smtpConfig['user'] == os.environ['TEST_SMTP_USERNAME']
        assert site.smtpConfig['password'] == os.environ['TEST_SMTP_USER_PASSWORD']
        assert site.smtpConfig['noreplyAddress'] == os.environ['TEST_SMTP_NO_REPLY']

    @pytest.mark.skipif(os.environ['SKIP_EMAILS'] == 'True',
                        reason="SKIP_EMAILS=True in test.ini")
    def test_test_smtp_config(self, site, admin_client, users):
        """ Sends a test email to admin user
        """
        response = admin_client.post(
                        "site/email/test-config",
                        data = {
                            'email': users['admin'].email,
                        },
                        follow_redirects=True,
                    )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html