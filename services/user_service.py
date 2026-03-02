from bcrypt import hashpw, gensalt
from models import User
from services.auth_service import get_user_permissions


def get_all_users(session):
    users = session.query(User).all()
    return [u.to_dict() for u in users]


def get_user_by_id(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('the user was not found')

    roles = [r.role for r in user.roles]
    permissions = get_user_permissions(user)
    data = user.to_dict()
    data['roles'] = roles
    data['permissions'] = permissions
    return data


def delete_user(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('the user was not found')

    # Protect superuser (first user)
    if user.id == 1:
        raise ValueError('you are not allowed to delete the superuser account')

    session.delete(user)
    session.commit()


def flush_users(session):
    session.query(User).filter(User.id > 1).delete()
    session.commit()


def reset_password(session, _id, password):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('the user was not found')

    user.password = hashpw(password.encode(), gensalt()).decode()
    session.commit()
    return user._id


def verify_user(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('the user was not found')

    user.verified = True
    session.commit()
    return user._id
