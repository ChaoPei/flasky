# -*- coding:utf-8 -*-

'''
路由模块
'''

from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, flash

from .. import db
from . import main
from .forms import NameForm
from ..models import User
from ..email import send_email


# 首页
@main.route('/', methods=['GET', 'POST'])   # 装饰器由蓝本提供
def index():
    form = NameForm()
    # POST请求
    if form.validate_on_submit():
        # 在数据库中查询用户名是否存在
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:        
            # 不存在则创建用户名
            flash('Welcome to create new user !')
            user = User(username=form.name.data)
            db.session.add(user)
            session['known'] = False
            
            # 发送邮件 
            if current_app.config['FLASKY_ADMIN']:
                send_email(current_app.config['FLASKY_ADMIN'], 'New User', 'mail/new_user', user=user)

        else:
            session['known'] = True
            
        
        # 保存在session中 
        session['name'] = form.name.data
        # 重定向为GET请求
        return redirect(url_for('.index'))      # 重定向url路径不一样, 使用蓝本的命名空间
    
    return render_template('index.html', form=form, name=session.get('name'),  
                           known=session.get('known', False), current_time=datetime.utcnow())


