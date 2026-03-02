from flask import Blueprint, request as req
from database import get_session
from validators.validators import (
    validate_role_name, validate_description, validate_permission
)
from services import role_service, module_service, permission_service
import responses

ori = Blueprint('ori', __name__, url_prefix='/ori')


# --- Role Management ---

@ori.route("/create_role/<role>/<description>", methods=['POST'])
def create_role(role, description):
    valid, msg = validate_role_name(role)
    if not valid:
        return responses.error(msg)

    valid, msg = validate_description(description)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        role_id = role_service.create_role(session, role, description)
        return responses.created('role created', dict(role_id=role_id))
    except ValueError as e:
        return responses.conflict(str(e))


@ori.route("/get_all_roles", methods=['POST'])
def get_all_roles():
    session = get_session()
    roles = role_service.get_all_roles(session)
    return responses.success('roles retrieved', dict(roles=roles))


@ori.route("/get_users_for_role/<role>", methods=['POST'])
def get_users_for_role(role):
    session = get_session()
    try:
        users = role_service.get_users_for_role(session, role)
        return responses.success('users retrieved', dict(users=users))
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/get_roles/<_id>", methods=['POST'])
def get_user_roles(_id):
    session = get_session()
    try:
        roles = role_service.get_user_roles(session, _id)
        return responses.success('roles retrieved', dict(roles=roles))
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/update_role/<orole>", methods=['POST'])
def update_role(orole):
    role = req.args.get('role', None)
    description = req.args.get('description', '')

    if role is None:
        return responses.error('there is no role name in your request')

    valid, msg = validate_role_name(role)
    if not valid:
        return responses.error(msg)

    valid, msg = validate_description(description)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        role_id = role_service.update_role(session, orole, role, description)
        return responses.success('role updated', dict(role_id=role_id))
    except LookupError as e:
        return responses.not_found(str(e))
    except ValueError as e:
        return responses.error(str(e))


@ori.route("/delete_role/<role>", methods=['DELETE'])
def delete_role(role):
    session = get_session()
    try:
        role_id = role_service.delete_role(session, role)
        return responses.success('role deleted', dict(id=role_id))
    except LookupError as e:
        return responses.not_found(str(e))
    except ValueError as e:
        return responses.error(str(e))


@ori.route("/assign_role/<_id>/<orole>", methods=['POST'])
def assign_role(_id, orole):
    session = get_session()
    try:
        msg = role_service.assign_role(session, _id, orole)
        return responses.success(msg)
    except LookupError as e:
        return responses.not_found(str(e))
    except ValueError as e:
        return responses.conflict(str(e))


@ori.route("/remove_role_from_user/<_id>/<role>", methods=['DELETE'])
def remove_role(_id, role):
    session = get_session()
    try:
        role_service.remove_role_from_user(session, _id, role)
        return responses.success('role removed')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/remove_all_roles_from_user/<_id>", methods=['POST'])
def remove_all_user_roles(_id):
    session = get_session()
    try:
        role_service.remove_all_roles_from_user(session, _id)
        return responses.success('all roles removed')
    except LookupError as e:
        return responses.not_found(str(e))
    except ValueError as e:
        return responses.error(str(e))


@ori.route("/flush_user_roles", methods=['POST'])
def flush_user_roles():
    session = get_session()
    role_service.flush_user_roles(session)
    return responses.success('user roles flushed')


# --- Module Management ---

@ori.route("/register_module/<name>/<description>", methods=['POST'])
def register_module(name, description=''):
    valid, msg = validate_role_name(name)
    if not valid:
        return responses.error(msg)

    valid, msg = validate_description(description)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        module_service.register_module(session, name, description)
        return responses.created('module successfully added')
    except ValueError as e:
        return responses.conflict(str(e))


@ori.route("/register_modules", methods=['POST'])
def register_modules():
    modules_dict = dict(req.args)

    for name in modules_dict.values():
        valid, msg = validate_role_name(name.strip().replace(' ', '_'))
        if not valid:
            return responses.error(f'one or more modules includes illegal characters')

    session = get_session()
    successful, failed = module_service.register_modules(session, modules_dict)
    return responses.success('completed', dict(success=successful, failed=failed))


@ori.route("/remove_module/<module>", methods=['POST'])
def remove_module(module):
    session = get_session()
    try:
        module_service.remove_module(session, module)
        return responses.success(f'{module.capitalize()} successfully removed')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/flush_modules", methods=['POST'])
def flush_modules():
    session = get_session()
    module_service.flush_modules(session)
    return responses.success('All modules successfully removed')


@ori.route("/get_modules", methods=['POST'])
def get_modules():
    session = get_session()
    modules = module_service.get_all_modules(session)
    return responses.success('modules retrieved', dict(modules=modules))


# --- Permissions Management ---

@ori.route("/set_role_permissions/<module>/<role>/<permission>", methods=['POST'])
def set_role_permissions(module, role, permission):
    valid, msg = validate_permission(permission)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        permission_service.set_role_permissions(session, module, role, int(permission))
        return responses.success('permissions updated')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/set_user_permissions/<module>/<_id>/<permission>", methods=['POST'])
def set_user_permissions(module, _id, permission):
    valid, msg = validate_permission(permission)
    if not valid:
        return responses.error(msg)

    session = get_session()
    try:
        permission_service.set_user_permissions(session, module, _id, int(permission))
        return responses.success('permissions updated')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/remove_role_permissions/<module>", methods=['POST'])
def remove_role_permissions(module):
    session = get_session()
    try:
        permission_service.remove_role_permissions(session, module)
        return responses.success('role permissions removed')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/flush_role_permissions", methods=['POST'])
def flush_role_permissions():
    session = get_session()
    permission_service.flush_role_permissions(session)
    return responses.success('all role permissions flushed')


@ori.route("/remove_user_permissions/<module>", methods=['POST'])
def remove_user_permissions(module):
    session = get_session()
    try:
        permission_service.remove_user_permissions(session, module)
        return responses.success('user permissions removed')
    except LookupError as e:
        return responses.not_found(str(e))


@ori.route("/flush_user_permissions", methods=['POST'])
def flush_user_permissions():
    session = get_session()
    permission_service.flush_user_permissions(session)
    return responses.success('all user permissions flushed')
