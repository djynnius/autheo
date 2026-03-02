from models import Module


def register_module(session, name, description=''):
    name = name.strip().replace(' ', '_').lower()
    description = description.strip()

    existing = session.query(Module).filter_by(module=name).first()
    if existing:
        raise ValueError('the module already exists')

    module = Module(module=name, description=description)
    session.add(module)
    session.commit()


def register_modules(session, modules_dict):
    """Register multiple modules in a single commit (batch instead of per-item)."""
    successful = []
    failed = []

    for name in modules_dict.values():
        name = name.strip().replace(' ', '_').lower()
        existing = session.query(Module).filter_by(module=name).first()
        if existing:
            failed.append(name)
            continue
        module = Module(module=name)
        session.add(module)
        successful.append(name)

    if successful:
        try:
            session.commit()
        except Exception:
            session.rollback()
            raise
    return successful, failed


def remove_module(session, module_name):
    module = session.query(Module).filter_by(module=module_name).one_or_none()
    if module is None:
        raise LookupError('module not found')

    session.delete(module)
    session.commit()


def flush_modules(session):
    session.query(Module).delete()
    session.commit()


def get_all_modules(session):
    modules = session.query(Module).all()
    return [m.to_dict() for m in modules]
