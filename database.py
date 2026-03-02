from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from models import Base

Session = scoped_session(sessionmaker())
_engine = None


def init_db(app, config):
    global _engine
    uri = config.DATABASE_URI
    connect_args = {}
    if uri.startswith('sqlite'):
        connect_args['check_same_thread'] = False
        _engine = create_engine(uri, connect_args=connect_args)
    else:
        _engine = create_engine(uri, pool_pre_ping=True)

    Session.configure(bind=_engine)

    @app.teardown_appcontext
    def remove_session(exception=None):
        Session.remove()

    return _engine


def get_session():
    return Session


def create_tables():
    Base.metadata.create_all(_engine)


def drop_tables():
    Base.metadata.drop_all(_engine)


def get_engine():
    return _engine
