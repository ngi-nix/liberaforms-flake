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
from flask_pymongo import PyMongo
from flask_babel import Babel


app = Flask(__name__)
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)
babel = Babel(app)

app.config['RESERVED_SLUGS'] = ['admin', 'admins', 'user', 'users', 'form', 'forms', 'site', 'sites']
app.config['RESERVED_FORM_ELEMENT_NAMES'] = ['created']

app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations;form_templates/translations'
app.config['LANGUAGES'] = {
    'en': ('English', 'en-US'),
    'ca': ('Català', 'es-ES'),
    'es': ('Castellano', 'es-ES')
}

import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/form_templates")

from GNGforms import views

if __name__ == '__main__':
        app.run()
