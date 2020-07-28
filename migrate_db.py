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

from gngforms import app
from gngforms.models import Installation

def migrate_db():
    installation=Installation.get()
    print("Schema version is {}".format(installation.schemaVersion))
    if not installation.isSchemaUpToDate():
        updated=installation.updateSchema()
        if updated:
            print("Migration completed OK")
            return True
        else:
            print("Error")
            print("Current database schema version is {} but should be {}".
                                                format( installation.schemaVersion,
                                                        app.config['SCHEMA_VERSION']))
            return False

    else:
        print("Database schema is already up to date")
        return True

if __name__ == '__main__':
    migrate_db()