from flask import jsonify
#from app.exceptions import ValidationError

from . import api


def bad_request(message):
    '''请求格式错误（404 是请求路径不存在
    '''
    response = jsonify({'error': 'bad request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    '''验证失败
    '''
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    '''权限不足
    '''
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


"""
@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
"""
