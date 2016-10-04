# -*- coding:utf-8 -*-

'''
使用蓝本来定义路由
'''

from flask import Blueprint

# 创建蓝本
main = Blueprint('main', __name__)

# 从当前目录导入路由和错误处理模块
from . import views, errors
