import requests as http_requests
from datetime import datetime, timezone
from bcrypt import gensalt, hashpw
from models import User, Role, OAuthAccount
from services.auth_service import tokenize, get_user_permissions

PROVIDERS = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'scope': 'openid email profile',
    },
    'github': {
        'authorize_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'scope': 'read:user user:email',
    },
    'discord': {
        'authorize_url': 'https://discord.com/api/oauth2/authorize',
        'token_url': 'https://discord.com/api/oauth2/token',
        'userinfo_url': 'https://discord.com/api/users/@me',
        'scope': 'identify email',
    },
}


def get_enabled_providers(config):
    enabled = []
    for name in PROVIDERS:
        client_id = getattr(config, f'{name.upper()}_CLIENT_ID', '')
        if client_id:
            enabled.append(name)
    return enabled


def build_authorize_url(provider, config):
    if provider not in PROVIDERS:
        raise ValueError(f'unknown provider: {provider}')

    client_id = getattr(config, f'{provider.upper()}_CLIENT_ID', '')
    if not client_id:
        raise ValueError(f'provider {provider} is not enabled')

    info = PROVIDERS[provider]
    redirect_uri = f'{config.OAUTH_REDIRECT_BASE}/ope/callback/{provider}'

    params = (
        f"client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={info['scope']}"
        f"&response_type=code"
    )
    return f"{info['authorize_url']}?{params}"


def exchange_code_for_token(provider, code, config):
    info = PROVIDERS[provider]
    client_id = getattr(config, f'{provider.upper()}_CLIENT_ID', '')
    client_secret = getattr(config, f'{provider.upper()}_CLIENT_SECRET', '')
    redirect_uri = f'{config.OAUTH_REDIRECT_BASE}/ope/callback/{provider}'

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }

    headers = {'Accept': 'application/json'}
    resp = http_requests.post(info['token_url'], data=data, headers=headers, timeout=10)
    resp.raise_for_status()
    body = resp.json()

    access_token = body.get('access_token')
    if not access_token:
        raise ValueError('token exchange failed: no access_token in response')
    return access_token


def fetch_user_profile(provider, access_token):
    info = PROVIDERS[provider]
    headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}
    resp = http_requests.get(info['userinfo_url'], headers=headers, timeout=10)
    resp.raise_for_status()
    profile = resp.json()

    if provider == 'google':
        return {
            'id': str(profile['id']),
            'email': profile.get('email'),
            'username': profile.get('name', '').lower().replace(' ', ''),
        }
    elif provider == 'github':
        email = profile.get('email')
        if not email:
            email_resp = http_requests.get(
                'https://api.github.com/user/emails',
                headers=headers, timeout=10
            )
            if email_resp.ok:
                emails = email_resp.json()
                primary = next((e for e in emails if e.get('primary')), None)
                email = primary['email'] if primary else None
        return {
            'id': str(profile['id']),
            'email': email,
            'username': (profile.get('login') or '').lower(),
        }
    elif provider == 'discord':
        return {
            'id': str(profile['id']),
            'email': profile.get('email'),
            'username': (profile.get('username') or '').lower(),
        }
    else:
        raise ValueError(f'unknown provider: {provider}')


def _unique_username(session, base_username):
    if not base_username:
        from helpers import _username
        return _username()

    candidate = base_username
    suffix = 0
    while session.query(User).filter_by(username=candidate).first() is not None:
        suffix += 1
        candidate = f'{base_username}_{suffix}'
    return candidate


def oauth_login(session, provider, code, config, jwt_expiry_days=7):
    access_token = exchange_code_for_token(provider, code, config)
    profile = fetch_user_profile(provider, access_token)

    provider_user_id = profile['id']
    email = profile.get('email')
    username = profile.get('username')

    # Check for existing OAuth link
    oauth_account = session.query(OAuthAccount).filter_by(
        provider=provider, provider_user_id=provider_user_id
    ).first()

    if oauth_account:
        # Returning user
        user = oauth_account.user
        oauth_account.provider_email = email
        oauth_account.provider_username = username
    else:
        # New OAuth login - check if email matches existing local user
        user = None
        if email:
            user = session.query(User).filter_by(email=email.lower()).first()

        if user is None:
            # Brand new user
            is_first = session.query(User).count() == 0
            admin_role = session.query(Role).filter_by(id=1).one() if is_first else None
            registered_role = session.query(Role).filter_by(id=2).one()

            user = User()
            user.username = _unique_username(session, username)
            user.email = (email or '').lower() or user.email  # keep default if no email
            user.verified = True
            user.secret = hashpw(str(datetime.now(timezone.utc)).encode(), gensalt())[2:32]

            session.add(user)

            if admin_role:
                user.roles.append(admin_role)
            user.roles.append(registered_role)

        oauth_account = OAuthAccount(
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            provider_username=username,
        )
        user.oauth_accounts.append(oauth_account)

    # Update login state
    last_login = user.last_login if user.last_login != user.created_at else None
    user.last_login = datetime.now(timezone.utc)
    user.status = True
    user.token = tokenize(user, jwt_expiry_days)

    session.commit()

    roles = [r.role for r in user.roles]
    permissions = get_user_permissions(user)

    return dict(
        _id=user._id,
        email=user.email,
        username=user.username,
        since=user.created_at.isoformat() if user.created_at else None,
        last_login=last_login.isoformat() if last_login else None,
        roles=roles,
        permissions=permissions,
        token=user.token,
        provider=provider,
    )
