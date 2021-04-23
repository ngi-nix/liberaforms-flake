"""
This file is part of LiberaForms.

# SPDX-FileCopyrightText: 2021 LiberaForms.org
# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import os
import pytest
from flask_migrate import Migrate, upgrade, stamp
from liberaforms import create_app
from liberaforms import db as _db


"""
Returns app
"""
@pytest.fixture(scope='session')
def app():
    flask_app = create_app()
    yield flask_app

"""
Upgrades database schema with alembic
Yields db
Drops tables
"""
@pytest.fixture(scope='session')
def db(app):
    migrate = Migrate(app, _db, directory='../migrations')
    with app.app_context():
        _db.drop_all()
        stamp(revision='base')
        upgrade()
        yield _db
        #_db.drop_all()
        #stamp(revision='base')

@pytest.fixture(scope='session')
def session(db):
    connection = db.engine.connect()
    #transaction = connection.begin()

    options = dict(bind=connection)
    session = db.create_scoped_session(options=options)
    db.session = session
    yield session

@pytest.fixture(scope='session')
def client(app):
    with app.test_client() as client:
        yield client

"""
@pytest.fixture(scope='function')
def session(request, db):
    session = db['session_factory']()
    yield session
    print('\n----- CREATE DB SESSION\n')

    session.rollback()
    session.close()
    print('\n----- ROLLBACK DB SESSION\n')
"""