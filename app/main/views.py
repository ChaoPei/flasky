# -*- coding:utf-8 -*-

'''
路由模块
'''

from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from .. import db
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm
from ..models import User, Role
from ..email import send_email
from ..decorators import admin_required


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


# 用户资料页面
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    return render_template('user.html', user=user)



# 编辑用户资料
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.realname
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', form=form)


# 管理员编辑用户资料
@main.route('/edit-profile<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):     # 传入用户id
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.realname = form.name.data
        user.location = form.location.data
        _user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated')
        return redirect(url_for('.user', username=current_user.username))
    # 表单默认显示的内容
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.realname
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template('edit_profile.html', form=form, user=user)



