# -*- coding:utf-8 -*-

'''
app包的构造文件, 导入大多数Flask的扩展包
延迟创建程序, 作为工厂函数
'''

# 导入扩展
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# 导入配置
from config import config



# 创建扩展实例
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

# 创建app并绑定扩展
def create_app(config_name):
    app = Flask(__name__)
    
    # 导入配置 
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    

    # 导入蓝本
    from .main import main as main_blueprint    # 只能在db初始化后导入, 不然构成循环依赖
    # 注册蓝本
    app.register_blueprint(main_blueprint)
    
    return app
