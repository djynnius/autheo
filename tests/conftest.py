import pytest
from autheo import create_app
from config import TestConfig
from database import get_session, create_tables, drop_tables
from models import Role


@pytest.fixture()
def app():
    config = TestConfig()
    app = create_app(config)
    app.config['TESTING'] = True

    with app.app_context():
        # Seed default roles
        session = get_session()
        admin = Role(role='administrator', description='The system administrator and superuser')
        registered = Role(role='registered', description='Registered user with login privileges')
        anon = Role(role='anonymous', description='Anonymous login with no privileges')
        session.add_all([admin, registered, anon])
        session.commit()

        yield app

        session.close()
        drop_tables()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    with app.app_context():
        return get_session()
