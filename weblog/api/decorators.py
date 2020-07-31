from functools import wraps
from flask import g

from .errors import forbidden
from ..models import Permission


def permission_required(permission):
    '''函数的返回值就是权限装饰器
    '''

    def wrapper(func):
        @wraps(func)
        def permission_func(*args, **kw):
            if not g.current_user.has_permission(permission):
                forbidden('Insufficient permissions')
            return func(*args, **kw)
        return permission_func
    return wrapper


write_required = permission_required(Permission.WRITE)
comment_required = permission_required(Permission.COMMENT)
