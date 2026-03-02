from flask import Blueprint, request as req
from database import get_session
from validators.validators import validate_username, validate_email, validate_password
from services import auth_service, user_service
import responses

ent = Blueprint('authentication', __name__, url_prefix='/ent')


@ent.route("/signup", methods=['POST'])
def signup():
    keys = list(req.form.keys())

    if 'password' not in keys:
        return responses.error('no password')

    if 'email' not in keys and 'username' not in keys:
        return responses.error('no username or email')

    username = req.form.get('username', '').strip()
    email = req.form.get('email', '').strip()
    password = req.form.get('password', '').strip()

    if username == '' and email == '':
        return responses.error('You must add at least one of email or username')

    if username != '':
        valid, msg = validate_username(username)
        if not valid:
            return responses.error(msg)

    if email != '':
        valid, msg = validate_email(email)
        if not valid:
            return responses.error(msg)

    valid, msg = validate_password(password)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        _id = auth_service.signup(session, username, email, password)
        return responses.created('user created', dict(_id=_id))
    except ValueError as e:
        return responses.conflict(str(e))


@ent.route("/login", methods=['POST'])
def login():
    username = req.form.get('username', '').strip().lower()
    email = req.form.get('email', '').strip().lower()

    if username == '' and email == '':
        return responses.error('no handle was provided')

    password = req.form.get('password', '')
    session = get_session()
    try:
        data = auth_service.login(session, username, email, password)
        return responses.success('authenticated', data)
    except LookupError as e:
        return responses.unauthorized(str(e))
    except ValueError as e:
        return responses.unauthorized(str(e))


@ent.route("/logout/<_id>", methods=['POST', 'GET'])
def logout(_id):
    session = get_session()
    try:
        auth_service.logout(session, _id)
        return responses.success('logged out', dict(_id=_id))
    except LookupError as e:
        return responses.not_found(str(e))


@ent.route('/get_users', methods=['POST', 'GET'])
def get_users():
    session = get_session()
    users = user_service.get_all_users(session)
    return responses.success('users retrieved', dict(users=users))


@ent.route('/get_user/<_id>', methods=['POST'])
def get_user(_id):
    session = get_session()
    try:
        data = user_service.get_user_by_id(session, _id)
        return responses.success('user retrieved', data)
    except LookupError as e:
        return responses.not_found(str(e))


@ent.route('/delete_user/<_id>', methods=['DELETE'])
def delete_user(_id):
    session = get_session()
    try:
        user_service.delete_user(session, _id)
        return responses.success('the user was deleted')
    except LookupError as e:
        return responses.not_found(str(e))
    except ValueError as e:
        return responses.error(str(e))


@ent.route('/flush_users', methods=['DELETE'])
def flush_users():
    session = get_session()
    user_service.flush_users(session)
    return responses.success('all users have been successfully deleted')


@ent.route("/reset_password/<_id>", methods=['PUT'])
def reset_password(_id):
    if 'password' not in req.form:
        return responses.error('no password')

    password = req.form.get('password', '').strip()
    valid, msg = validate_password(password)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        uid = user_service.reset_password(session, _id, password)
        return responses.success(f'password for {uid} successfully updated')
    except LookupError as e:
        return responses.not_found(str(e))


@ent.route("/verify/<_id>", methods=['PUT'])
def verify(_id):
    session = get_session()
    try:
        uid = user_service.verify_user(session, _id)
        return responses.success(f'user {uid} was successfully verified')
    except LookupError as e:
        return responses.not_found(str(e))
