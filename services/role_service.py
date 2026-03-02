from models import User, Role, user_roles


def create_role(session, role_name, description):
    role_name = role_name.strip().replace(' ', '_').lower()
    description = description.strip()

    existing = session.query(Role).filter_by(role=role_name).first()
    if existing:
        raise ValueError('the role already exists')

    new_role = Role(role=role_name, description=description)
    session.add(new_role)
    session.commit()

    return new_role.id


def get_all_roles(session):
    roles = session.query(Role).all()
    return [r.to_dict() for r in roles]


def get_users_for_role(session, role_name):
    role = session.query(Role).filter_by(role=role_name).one_or_none()
    if role is None:
        raise LookupError('this role does not exist')
    return [dict(_id=u._id, username=u.username, email=u.email) for u in role.users]


def get_user_roles(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user not found')
    return [dict(id=r.id, role=r.role) for r in user.roles]


def update_role(session, old_name, new_name, description):
    new_name = new_name.strip().replace(' ', '_').lower()
    description = description.strip()

    role = session.query(Role).filter_by(role=old_name).one_or_none()
    if role is None:
        raise LookupError('the role you want to update does not exist')

    if role.id in (1, 2, 3):
        raise ValueError('you cannot edit/update the base roles')

    role.role = new_name
    role.description = description
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise ValueError('the role name you are updating to already exists')

    return role.id


def delete_role(session, role_name):
    role = session.query(Role).filter_by(role=role_name).one_or_none()
    if role is None:
        raise LookupError('the role you want to delete does not exist')

    if role.id in (1, 2, 3):
        raise ValueError('you cannot delete the base roles')

    role_id = role.id
    session.delete(role)
    session.commit()  # Fixes bug #4 - was missing commit
    return role_id


def assign_role(session, _id, role_name):
    role = session.query(Role).filter_by(role=role_name).one_or_none()
    if role is None:
        raise LookupError('this role does not exist')

    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user not found')

    if role_name in [r.role for r in user.roles]:
        raise ValueError('this role has already been assigned')

    user.roles.append(role)
    session.commit()
    return f'role of {role_name} successfully assigned to {_id}'  # Fixes typo "assgned"


def remove_role_from_user(session, _id, role_name):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user not found')

    role = session.query(Role).filter_by(role=role_name).one_or_none()
    if role is None:
        raise LookupError('role not found')

    user.roles.remove(role)
    session.commit()


def remove_all_roles_from_user(session, _id):
    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user not found')

    if user.id == 1:
        raise ValueError('cannot remove roles from superuser')

    user.roles = []
    session.commit()


def flush_user_roles(session):
    # Fixes bug #5 - uses proper delete on junction table instead of referencing nonexistent id column
    session.execute(user_roles.delete())
    session.commit()
