# -*- coding:utf-8 -*-

'''
保存配置
'''

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'l love zhangfan'  # 私密配置从环境变量导入
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    
    # 邮件设置  
    FLASK_MAIL_SUBJECT_PREFIX = '[Flasky]'          # 邮件主题前缀
    FLASK_MAIL_SENDER = 'peichao_hainu@163.com'     # 收件人
    FLASK_ADMIN = os.environ.get('FLASKY_ADMIN')
    MAIL_SERVER = 'peichao_pku@163.com'             # 发件人
    MAIL_PORT = 25 #SSL 465
    MAIL_USR_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    @staticmethod
    def init_app(app):
        pass

# 部署配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


# 测试配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
