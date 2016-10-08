# -*- coding:utf-8 -*-

'''
权限装饰器, 装饰路由函数, 检查当前用户权限是否能够访问路由函数的页面
'''
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator



def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)

