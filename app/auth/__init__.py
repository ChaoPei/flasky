# -*- coding:utf-8 -*-

'''
用户认证
'''

from flask import Blueprint

# 用户认证蓝本
auth = Blueprint('auth', __name__)

from . import views
