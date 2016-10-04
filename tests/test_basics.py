# -*- coding:utf-8 -*-

'''
基础单元测试
'''

import unittest
from flask import current_app
from app import create_app, db

class BasicsTestCase(unittest.TestCase):
    # 初始化, 建立测试环境
    def setUp(self):
        self.app = create_app('testing') # 创建程序实例
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all() # 创建数据库
    
    # 退出清理, 删除数据库和程序上下文 
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    

    # 测试程序实例存在
    def test_app_exists(self):
        self.assertFalse(current_app is None)
    
    # 测试配置是否为TESTING
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
        
