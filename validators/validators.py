import re


def validate_username(username):
    if not username or len(username.strip()) == 0:
        return False, 'username is required'
    username = username.strip()
    if len(username) < 8:
        return False, 'username is less than 8 characters long'
    if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9]+)$', username) is None:
        return False, ('username can only contain numbers and letters, underscore and dot. '
                       'username cannot start with a number, underscore or dot '
                       'nor can it end with a dot or underscore')
    return True, None


def validate_email(email):
    if not email or len(email.strip()) == 0:
        return False, 'email is required'
    email = email.strip()
    if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9]+)@([a-zA-Z]+)\.([a-zA-Z.]{2,5})$', email) is None:
        return False, 'this is not a valid email'
    return True, None


def validate_password(password):
    if not password or len(password.strip()) == 0:
        return False, 'no password'
    password = password.strip()
    if len(password) < 8:
        return False, 'password is less than 8 characters long'
    if (re.search(r'[a-z]+', password) is None or
            re.search(r'[A-Z]+', password) is None or
            re.search(r'[0-9]+', password) is None or
            re.search(r'[_.$@*!+#%&-]+', password) is None):
        return False, 'password must contain lowercase, uppercase, number and special character'
    return True, None


def validate_role_name(name):
    if not name or len(name.strip()) == 0:
        return False, 'role name is required'
    if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_]*)$', name.strip()) is None:
        return False, 'the role includes illegal characters'
    return True, None


def validate_description(description):
    if not description or len(description.strip()) == 0:
        return False, 'description is required'
    if re.search(r'^([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]*)$', description.strip()) is None:
        return False, 'the description includes illegal characters'
    return True, None


def validate_permission(permission):
    try:
        p = int(permission)
    except (ValueError, TypeError):
        return False, 'permission must be a number'
    if p < 0 or p > 7:
        return False, 'permission must be between 0 and 7'
    return True, None
