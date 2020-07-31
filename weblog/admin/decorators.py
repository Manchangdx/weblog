from functools import wraps
from flask import abort, flash
from flask_login import current_user

from ..models import Permission


def permission_required(permission):
    '''嵌套函数，返回值为各种装饰器'''

    def decorator(func):
        @wraps(func)
        def decorated_func(*args, **kw):
            if not current_user.role.permissions & permission:
                flash('你这个号级别不够啊！', 'warning')
                abort(403)
            return func(*args, **kw)
        return decorated_func

    return decorator


admin_required = permission_required(Permission.ADMINISTER)
moderate_required = permission_required(Permission.MODERATE)
comment_required = permission_required(Permission.COMMENT)
