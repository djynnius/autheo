from unittest.mock import patch, MagicMock


# --- Provider listing ---

def test_no_providers_enabled_by_default(client):
    resp = client.get('/ope/providers')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['data']['providers'] == []


def test_google_shows_when_configured(app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'test-google-id'
    resp = client.get('/ope/providers')
    data = resp.get_json()
    assert 'google' in data['data']['providers']


# --- Login redirect ---

def test_login_unknown_provider(client):
    resp = client.get('/ope/login/fakeprovider')
    assert resp.status_code == 400
    assert 'unknown provider' in resp.get_json()['message']


def test_login_disabled_provider(client):
    resp = client.get('/ope/login/google')
    assert resp.status_code == 400
    assert 'not enabled' in resp.get_json()['message']


def test_login_google_redirects(app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'test-google-id'
    resp = client.get('/ope/login/google')
    assert resp.status_code == 302
    assert 'accounts.google.com' in resp.headers['Location']
    assert 'test-google-id' in resp.headers['Location']


# --- Callback ---

def test_callback_missing_code(client):
    resp = client.get('/ope/callback/google')
    assert resp.status_code == 400
    assert 'missing code' in resp.get_json()['message']


def _mock_token_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'access_token': 'mock-token'}
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _mock_google_profile():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'id': 'google-123',
        'email': 'alice@gmail.com',
        'name': 'Alice Test',
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _mock_github_profile():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'id': 456,
        'login': 'alicehub',
        'email': 'alice@github.com',
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def _mock_discord_profile():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        'id': '789',
        'username': 'alicecord',
        'email': 'alice@discord.com',
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@patch('services.oauth_service.http_requests')
def test_google_new_user(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'gid'
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_SECRET = 'gsec'

    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_google_profile()

    resp = client.get('/ope/callback/google?code=authcode123')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['provider'] == 'google'
    assert data['email'] == 'alice@gmail.com'
    assert data['token']
    assert 'administrator' in data['roles']  # first user gets admin


@patch('services.oauth_service.http_requests')
def test_github_new_user(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].GITHUB_CLIENT_ID = 'ghid'
    app.config['AUTHEO_CONFIG'].GITHUB_CLIENT_SECRET = 'ghsec'

    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_github_profile()

    resp = client.get('/ope/callback/github?code=authcode456')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['provider'] == 'github'
    assert data['username'] == 'alicehub'
    assert 'administrator' in data['roles']


@patch('services.oauth_service.http_requests')
def test_discord_new_user(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].DISCORD_CLIENT_ID = 'did'
    app.config['AUTHEO_CONFIG'].DISCORD_CLIENT_SECRET = 'dsec'

    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_discord_profile()

    resp = client.get('/ope/callback/discord?code=authcode789')
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['provider'] == 'discord'
    assert data['username'] == 'alicecord'


@patch('services.oauth_service.http_requests')
def test_returning_user_same_id(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'gid'
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_SECRET = 'gsec'

    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_google_profile()

    # First login
    resp1 = client.get('/ope/callback/google?code=code1')
    id1 = resp1.get_json()['data']['_id']

    # Second login - same provider user id, same local user
    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_google_profile()
    resp2 = client.get('/ope/callback/google?code=code2')
    id2 = resp2.get_json()['data']['_id']

    assert id1 == id2


@patch('services.oauth_service.http_requests')
def test_email_links_to_existing_password_user(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'gid'
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_SECRET = 'gsec'

    # Create a password user first (username must be >=8 chars)
    signup_resp = client.post('/ent/signup', data={
        'email': 'alice@gmail.com',
        'password': 'MyPass123!',
    })
    assert signup_resp.status_code == 201
    original_id = signup_resp.get_json()['data']['_id']

    mock_http.post.return_value = _mock_token_response()
    mock_http.get.return_value = _mock_google_profile()

    resp = client.get('/ope/callback/google?code=code1')
    data = resp.get_json()['data']
    assert data['email'] == 'alice@gmail.com'
    assert data['_id'] == original_id  # linked to existing user, not a new one


@patch('services.oauth_service.http_requests')
def test_token_exchange_failure(mock_http, app, client):
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_ID = 'gid'
    app.config['AUTHEO_CONFIG'].GOOGLE_CLIENT_SECRET = 'gsec'

    import requests
    mock_http.post.side_effect = requests.exceptions.HTTPError('401 Unauthorized')

    resp = client.get('/ope/callback/google?code=badcode')
    assert resp.status_code == 502
    assert 'OAuth login failed' in resp.get_json()['message']


def test_password_login_blocked_for_oauth_user(app, client):
    """OAuth-only users (no password) get a clear error on /ent/login."""
    from database import get_session
    from models import User, Role
    from bcrypt import gensalt, hashpw
    from datetime import datetime, timezone

    with app.app_context():
        session = get_session()
        user = User()
        user.username = 'oauthonly'
        user.email = 'oauthonly@example.com'
        user.password = None
        user.verified = True
        user.secret = hashpw(str(datetime.now(timezone.utc)).encode(), gensalt())[2:32]
        registered = session.query(Role).filter_by(id=2).one()
        session.add(user)
        user.roles.append(registered)
        session.commit()

    resp = client.post('/ent/login', data={
        'username': 'oauthonly',
        'password': 'anything',
    })
    assert resp.status_code == 401
    assert 'OAuth' in resp.get_json()['message']
