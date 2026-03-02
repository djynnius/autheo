from flask import jsonify


def _response(status, message, data, status_code):
    body = dict(status=status, message=message)
    if data is not None:
        body['data'] = data
    return jsonify(body), status_code


def success(message='Success', data=None, status_code=200):
    return _response('success', message, data, status_code)


def created(message='Created', data=None):
    return _response('success', message, data, 201)


def error(message='Bad request', status_code=400):
    return _response('error', message, None, status_code)


def not_found(message='Not found'):
    return _response('error', message, None, 404)


def conflict(message='Conflict'):
    return _response('error', message, None, 409)


def unauthorized(message='Unauthorized'):
    return _response('error', message, None, 401)
