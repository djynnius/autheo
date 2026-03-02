from models import Module, Role, User, ModuleRole, ModuleUser


def set_role_permissions(session, module_name, role_name, permission):
    module_name = module_name.strip().lower()
    role_name = role_name.strip().lower()
    permission = int(permission)

    module = session.query(Module).filter(Module.module.ilike(module_name)).one_or_none()
    if module is None:
        raise LookupError('module does not exist')

    role = session.query(Role).filter_by(role=role_name).one_or_none()
    if role is None:
        raise LookupError('role does not exist')

    # Upsert via ORM (fixes bugs #2, #3, #11)
    mr = session.query(ModuleRole).filter_by(
        module_id=module.id, role_id=role.id
    ).one_or_none()

    if mr is None:
        mr = ModuleRole(module_id=module.id, role_id=role.id, permissions=permission)
        session.add(mr)
    else:
        mr.permissions = permission

    session.commit()


def set_user_permissions(session, module_name, _id, permission):
    """Fixes bug #2: parameter correctly named module_name (not module_id)."""
    module_name = module_name.strip().lower()
    permission = int(permission)

    module = session.query(Module).filter(Module.module.ilike(module_name)).one_or_none()
    if module is None:
        raise LookupError('module does not exist')

    user = session.query(User).filter_by(_id=_id).one_or_none()
    if user is None:
        raise LookupError('user does not exist')

    # Upsert via ORM (fixes bug #3 - mrs[0].id should be mus[0].id)
    mu = session.query(ModuleUser).filter_by(
        module_id=module.id, user_id=user.id
    ).one_or_none()

    if mu is None:
        mu = ModuleUser(module_id=module.id, user_id=user.id, permissions=permission)
        session.add(mu)
    else:
        mu.permissions = permission

    session.commit()


def remove_role_permissions(session, module_name):
    module = session.query(Module).filter(Module.module.ilike(module_name)).one_or_none()
    if module is None:
        raise LookupError('module does not exist')

    session.query(ModuleRole).filter_by(module_id=module.id).delete()
    session.commit()


def flush_role_permissions(session):
    session.query(ModuleRole).delete()
    session.commit()


def remove_user_permissions(session, module_name):
    module = session.query(Module).filter(Module.module.ilike(module_name)).one_or_none()
    if module is None:
        raise LookupError('module does not exist')

    session.query(ModuleUser).filter_by(module_id=module.id).delete()
    session.commit()


def flush_user_permissions(session):
    session.query(ModuleUser).delete()
    session.commit()
