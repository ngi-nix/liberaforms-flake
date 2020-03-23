"""
“Copyright 2020 La Coordinadora d’Entitats per la Lleialtat Santsenca”

This file is part of GNGforms.

GNGforms is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from urllib.parse import urlparse
from flask import request, render_template, redirect
from flask import g, session, flash, Blueprint
from flask_wtf.csrf import CSRFError

from GNGforms import app
from GNGforms.models import Site, User
from GNGforms.utils.wraps import *
from GNGforms.utils.utils import *
import GNGforms.utils.wtf as wtf

main_bp = Blueprint('main_bp', __name__,
                    template_folder='../templates/main')

@app.before_request
def before_request():
    g.site=None
    g.current_user=None
    g.isRootUser=False
    g.isAdmin=False
    if request.path[0:7] == '/static':
        return
    g.site=Site.find(hostname=urlparse(request.host_url).hostname)
    if 'user_id' in session and session["user_id"] != None:
        g.current_user=User.find(id=session["user_id"], hostname=g.site.hostname)
        if not g.current_user:
            session.pop("user_id")
            return
        if g.current_user.isRootUser():
            g.isRootUser=True
        if g.current_user.isAdmin():
            g.isAdmin=True


@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html', site=g.site, wtform=wtf.Login())

@app.errorhandler(404)
def page_not_found(error):
    print('404!!!!')
    return render_template('page-not-found.html'), 400

@app.errorhandler(500)
def server_error(error):
    return render_template('server-error.html'), 500

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(e.description, 'error')
    return redirect(make_url_for('main_bp.index'))



@enabled_user_required
@main_bp.route('/test', methods=['GET'])
def test():
    return render_template('test.html', sites=[])