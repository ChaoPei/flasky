# -*- coding:utf-8 -*-

'''
使用蓝本来定义路由
蓝本可以定义路由, 然后将蓝本注册到app中
'''

from flask import Blueprint

# 创建蓝本
main = Blueprint('main', __name__)

# 从当前目录导入路由和错误处理模块
from . import views, errors


from ..models import Permission 

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
