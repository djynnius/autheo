import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_BACKEND = os.environ.get('AUTHEO_DB_BACKEND', 'sqlite')
    DB_HOST = os.environ.get('AUTHEO_DB_HOST', 'localhost')
    DB_PORT = os.environ.get('AUTHEO_DB_PORT', '')
    DB_NAME = os.environ.get('AUTHEO_DB_NAME', 'autheo')
    DB_USER = os.environ.get('AUTHEO_DB_USER', '')
    DB_PASSWORD = os.environ.get('AUTHEO_DB_PASSWORD', '')
    DB_PATH = os.environ.get('AUTHEO_DB_PATH', 'dbs/autheo.db')
    JWT_EXPIRY_DAYS = int(os.environ.get('AUTHEO_JWT_EXPIRY_DAYS', '7'))
    PORT = int(os.environ.get('AUTHEO_PORT', '8800'))
    HOST = os.environ.get('AUTHEO_HOST', '0.0.0.0')
    DEBUG = os.environ.get('AUTHEO_DEBUG', 'true').lower() == 'true'

    # OAuth provider credentials (provider is enabled when CLIENT_ID is non-empty)
    GOOGLE_CLIENT_ID = os.environ.get('AUTHEO_GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('AUTHEO_GOOGLE_CLIENT_SECRET', '')
    GITHUB_CLIENT_ID = os.environ.get('AUTHEO_GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.environ.get('AUTHEO_GITHUB_CLIENT_SECRET', '')
    DISCORD_CLIENT_ID = os.environ.get('AUTHEO_DISCORD_CLIENT_ID', '')
    DISCORD_CLIENT_SECRET = os.environ.get('AUTHEO_DISCORD_CLIENT_SECRET', '')
    OAUTH_REDIRECT_BASE = os.environ.get('AUTHEO_OAUTH_REDIRECT_BASE', 'http://localhost:8800')

    @property
    def DATABASE_URI(self):
        backend = self.DB_BACKEND.lower()
        if backend == 'sqlite':
            return f'sqlite:///{self.DB_PATH}'
        elif backend == 'postgres':
            port = self.DB_PORT or '5432'
            return f'postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{port}/{self.DB_NAME}'
        elif backend in ('mysql', 'mariadb'):
            port = self.DB_PORT or '3306'
            return f'mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{port}/{self.DB_NAME}'
        elif backend == 'duckdb':
            return f'duckdb:///{self.DB_PATH}'
        else:
            raise ValueError(f'Unsupported database backend: {backend}')


class TestConfig(Config):
    DEBUG = True
    DB_BACKEND = 'sqlite'

    @property
    def DATABASE_URI(self):
        return 'sqlite:///:memory:'
