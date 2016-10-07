# -*- coding: utf-8 -*-

'''
用户认证路由
'''

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user


# 导入认证蓝本
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db
from ..email import send_email



# 登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():   # POST请求
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    
    return render_template('auth/login.html', form=form)    # GET请求


# 登出
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))



# 注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data,
                password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm your accout', 'auth/email/confirm', user=user, token=token);
        flash('A confirm email has been sent to you by email')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


# 确认用户账户
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('Confirmed your account successfully, thanks!')
    else:
        flash('The confirmation link is invalid or has expired')
    return redirect(url_for('main.index'))


# 钩子程序, 限制未确认用户能够访问的权限
@auth.before_app_request    # 针对全局程序请求
def before_request():
    # 用户已登录, 未激活, 访问非auth内的端点是不允许的
    if current_user.is_authenticated and not current_user.confirmed and request.endpoint[:5] != 'auth.' and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


# 未确认页面
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


# 重新发送确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm you accout', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to your by email.')
    return redirect(url_for('main.index'))


