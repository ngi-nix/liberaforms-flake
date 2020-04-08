"""
“Copyright 2019 La Coordinadora d’Entitats per la Lleialtat Santsenca”

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

from flask import Flask
from flask_mongoengine import MongoEngine
from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
import sys, os


app = Flask(__name__)
app.config.from_pyfile('../config.cfg')
db = MongoEngine(app)
babel = Babel(app)

csrf = CSRFProtect()
csrf.init_app(app)

app.config['APP_VERSION'] = "1.1.0"
app.config['SCHEMA_VERSION'] = 14

app.config['RESERVED_SLUGS'] = ['login', 'static', 'admin', 'admins', 'user', 'users',
                                'form', 'forms', 'site', 'sites', 'update']
# DPL = Data Protection Law
app.config['RESERVED_FORM_ELEMENT_NAMES'] = ['created', 'csrf_token', 'DPL']
app.config['RESERVED_USERNAMES'] = ['system', 'admin']

app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations;form_templates/translations'
app.config['LANGUAGES'] = {
    'en': ('English', 'en-US'),
    'ca': ('Català', 'es-ES'),
    'es': ('Castellano', 'es-ES')
}
app.config['FAVICON_FOLDER'] = "%s/static/images/favicon/" % os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")


from gngforms.views.main import main_bp
from gngforms.views.user import user_bp
from gngforms.views.form import form_bp
from gngforms.views.site import site_bp
from gngforms.views.admin import admin_bp
from gngforms.views.entries import entries_bp

app.register_blueprint(main_bp)
app.register_blueprint(user_bp)
app.register_blueprint(form_bp)
app.register_blueprint(site_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(entries_bp)


if __name__ == '__main__':
    app.run()