"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from liberaforms.models.user import User
from liberaforms.models.formuser import FormUser
from .utils import login, logout

class TestFormAdminSettings():
    def test_disable_form(self, client, anon_client, users, forms):
        """ Tests disable form
            Test permissions
        """
        form_id = forms['test_form'].id
        url = f"/admin/forms/toggle-public/{form_id}"
        response = anon_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        login(client, users['editor'])
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- site_index_page -->' in html
        logout(client)
        login(client, users['admin'])
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].adminPreferences['public'] == False
        assert forms['test_form'].is_public() == False
        response = anon_client.get(
                            f"/{forms['test_form'].slug}",
                            follow_redirects=True
                        )
        assert response.status_code == 404
        html = response.data.decode()
        assert '<!-- page_not_found_404 -->' in html
        forms['test_form'].adminPreferences['public'] = True
        forms['test_form'].save()

    def test_change_author(self, client, anon_client, forms, users):
        """ Tests nonexistent username and valid username
            Tests permission
        """
        form_id = forms['test_form'].id
        url = f"/admin/forms/change-author/{form_id}"
        response = anon_client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- site_index_page -->' in response.data.decode()
        login(client, users['editor'])
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- site_index_page -->' in response.data.decode()
        logout(client)
        login(client, users['admin'])
        response = client.get(
                            url,
                            follow_redirects=True
                        )
        assert response.status_code == 200
        assert '<!-- change_author_page -->' in response.data.decode()
        initial_author = forms['test_form'].author
        assert FormUser.find(form_id=forms['test_form'].id,
                             user_id=forms['test_form'].author_id) != None
        nonexistent_username = "nonexistent"
        response = client.post(
                            url,
                            data = {
                                "old_author_username": initial_author.username,
                                "new_author_username": nonexistent_username,
                            },
                            follow_redirects=False
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<!-- change_author_page -->' in html
        assert '<div class="warning flash_message">' in html

        # TODO. Test change author to the alread existing author
        #assert g.current.username != initial_author.username

        # we use the dummy_1 user to be the new author
        dummy_1 = User.find(username=users['dummy_1']['username'])
        response = client.post(
                            url,
                            data = {
                                "old_author_username": initial_author.username,
                                "new_author_username": dummy_1.username,
                            },
                            follow_redirects=True
                        )
        assert response.status_code == 200
        html = response.data.decode()
        assert '<div class="success flash_message">' in html
        assert '<!-- inspect_form_page -->' in html
        assert forms['test_form'].author.id == dummy_1.id
        assert FormUser.find(form_id=forms['test_form'].id,
                             user_id=dummy_1.id) != None
        # reset author to initial value to continue testing
        response = client.post(
                            url,
                            data = {
                                "old_author_username": dummy_1.username,
                                "new_author_username": initial_author.username,
                            }
                        )
        # Note: dummy_1 is now an editor
