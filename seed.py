"""Database initialization script. Creates tables and seeds default roles."""
from flask import Flask
from config import Config
from database import init_db, create_tables, get_session
from models import Role


def seed():
    app = Flask(__name__)
    config = Config()
    init_db(app, config)
    create_tables()

    with app.app_context():
        session = get_session()

        # Only seed if roles table is empty
        if session.query(Role).count() == 0:
            admin = Role(role='administrator', description='The system administrator and superuser')
            registered = Role(role='registered', description='Registered user with login privileges')
            anon = Role(role='anonymous', description='Anonymous login with no privileges')
            session.add_all([admin, registered, anon])
            session.commit()
            print('Seeded 3 default roles: administrator, registered, anonymous')
        else:
            print('Roles already exist, skipping seed')

    print('Database initialized successfully')


if __name__ == '__main__':
    seed()
