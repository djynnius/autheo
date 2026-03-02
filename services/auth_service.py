import jwt
from bcrypt import hashpw, checkpw, gensalt
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_
from models import User, Role


def signup(session, username, email, password, jwt_expiry_days=7):
    username = (username or '').strip().lower()
    email = (email or '').strip().lower()
    password = (password or '').strip()

    # Check if user already exists via ORM (fixes SQL injection)
    filters = []
    if username:
        filters.append(User.username == username)
    if email:
        filters.append(User.email == email)
    existing = session.query(User).filter(or_(*filters)).first()
    if existing:
        raise ValueError('a user with these credentials already exists')

    user = User()
    if username:
        user.username = username
    if email:
        user.email = email
    user.password = hashpw(password.encode(), gensalt()).decode()
    user.secret = hashpw(str(datetime.now(timezone.utc)).encode(), gensalt())[2:32]

    # Check if this is the first user BEFORE adding (fixes bug #6)
    is_first = session.query(User).count() == 0
    admin_role = session.query(Role).filter_by(id=1).one() if is_first else None
    registered_role = session.query(Role).filter_by(id=2).one()

    user.token = init_token(user, jwt_expiry_days)

    session.add(user)

    if admin_role:
        user.roles.append(admin_role)
    user.roles.append(registered_role)

    session.commit()

    return user._id


def login(session, username, email, password, jwt_expiry_days=7):
    username = (username or '').strip().lower()
    email = (email or '').strip().lower()

    if not username and not email:
        raise ValueError('no handle was provided')

    if email:
        user = session.query(User).filter_by(email=email).one_or_none()
    else:
        user = session.query(User).filter_by(username=username).one_or_none()

    if user is None:
        raise LookupError('user does not exist')

    if user.password is None:
        raise ValueError('this account uses OAuth login')

    if not checkpw(password.encode(), user.password.encode()):
        raise ValueError('authentication failed')

    roles = [r.role for r in user.roles]
    permissions = get_user_permissions(user)

    last_login = user.last_login if user.last_login != user.created_at else None
    user.last_login = datetime.now(timezone.utc)
    user.status = True
    user.token = tokenize(user, jwt_expiry_days)

    session.commit()

    return dict(
        _id=user._id,
        email=user.email,
        username=user.username,
        since=user.created_at.isoformat() if user.created_at else None,
        last_login=last_login.isoformat() if last_login else None,
        roles=roles,
        permissions=permissions,
        token=user.token,
    )


def logout(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user does not exist')

    user.status = False
    user.token = reset_token(user)
    session.commit()
    return _id


def get_user_permissions(user):
    """Pure ORM replacement for the raw SQL UNION permissions query."""
    permissions = {}
    for role in user.roles:
        for mp in role.module_permissions:
            key = mp.module.module
            permissions[key] = max(permissions.get(key, 0), mp.permissions or 0)
    for mp in user.module_permissions:
        key = mp.module.module
        permissions[key] = max(permissions.get(key, 0), mp.permissions or 0)
    return [dict(module=k, permissions=v) for k, v in permissions.items()]


def tokenize(user, expiry_days=7):
    try:
        decoded = jwt.decode(user.token, user.secret, algorithms=["HS256"])
        exp = datetime.fromisoformat(decoded['exp']) if isinstance(decoded['exp'], str) else datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        if exp > datetime.now(timezone.utc):
            return user.token
    except Exception:
        pass

    payload = dict(
        iat=datetime.now(timezone.utc),
        exp=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        username=user.username,
        email=user.email,
        _id=user._id,
    )
    return jwt.encode(payload, user.secret, algorithm="HS256")


def reset_token(user, expiry_days=7):
    payload = dict(
        iat=datetime.now(timezone.utc),
        exp=datetime.now(timezone.utc) + timedelta(days=expiry_days),
        username=user.username,
        email=user.email,
        _id=user._id,
    )
    return jwt.encode(payload, user.secret, algorithm="HS256")


def init_token(user, expiry_days=7):
    payload = dict(
        iat=datetime.now(timezone.utc),
        exp=datetime.now(timezone.utc) - timedelta(days=expiry_days),
        username=user.username,
        email=user.email,
        _id=user._id,
    )
    return jwt.encode(payload, user.secret, algorithm="HS256")
