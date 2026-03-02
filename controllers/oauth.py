from flask import Blueprint, redirect, request as req
from database import get_session
from services import oauth_service
import responses

ope = Blueprint('oauth', __name__, url_prefix='/ope')


@ope.route('/providers', methods=['GET'])
def providers():
    from flask import current_app
    config = current_app.config['AUTHEO_CONFIG']
    enabled = oauth_service.get_enabled_providers(config)
    return responses.success('enabled providers', dict(providers=enabled))


@ope.route('/login/<provider>', methods=['GET'])
def login(provider):
    from flask import current_app
    config = current_app.config['AUTHEO_CONFIG']
    try:
        url = oauth_service.build_authorize_url(provider, config)
        return redirect(url)
    except ValueError as e:
        return responses.error(str(e))


@ope.route('/callback/<provider>', methods=['GET'])
def callback(provider):
    from flask import current_app
    config = current_app.config['AUTHEO_CONFIG']

    code = req.args.get('code')
    if not code:
        return responses.error('missing code parameter')

    session = get_session()
    try:
        data = oauth_service.oauth_login(
            session, provider, code, config, config.JWT_EXPIRY_DAYS
        )
        return responses.success('authenticated', data)
    except ValueError as e:
        return responses.error(str(e))
    except Exception as e:
        return responses.error(f'OAuth login failed: {e}', status_code=502)
