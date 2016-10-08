# -*- coding:utf-8 -*-

'''
数据库表
'''


from . import db
from . import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import db

from datetime import datetime


# 权限常量
class Permission:
    FOLLOW = 0x01   # 关注其他用户
    COMMENT = 0x02   # 评论
    WRITE_ARTICLES = 0x04   # 发表文章
    MODERATE_COMMENTS = 0x08    # 管理他人的评论
    ADMINISTER = 0x80   # 管理员


# 角色
class Role(db.Model):
    
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    rolename = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)  # 默认角色是User
    permissions = db.Column(db.Integer)     # 不同位表示不同的权限, 目前只有5个权限, 所以只占用5位
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.rolename

    
    # 在数据库中创建角色
    @staticmethod
    def insert_roles():
        roles = {
                'User': (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
                'Moderator': (Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS, False),
                'Administrator': (0xff, False)
                }
        for r in roles:
            role = Role.query.filter_by(rolename=r).first()
            if role is None:
                role = Role(rolename=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


# 用户
class User(UserMixin, db.Model):    # UserMixin实现了Flask-Login要求必须实现的用户方法
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))   # 散列密码 
    confirmed = db.Column(db.Boolean, default=False) # 是否激活(邮件确认)
    
    # 用户资料页面字段
    realname = db.Column(db.String(64))     # 真实姓名
    location = db.Column(db.String(64))     # 位置
    about_me = db.Column(db.Text())         # 关于
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)    # 注册时间
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)       # 最后登录时间


    def __repr__(self):
        return '<User %r>' % self.username
 
    
    # 赋予角色
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
     
    @property
    def password(self):
        raise AttributeError('password can not access!')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # 生成确认令牌
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})
    
    # 校验令牌
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
            print 'try: ', data
        except:
            print 'excepte'
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    # 生成重置令牌
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})
    
    # 重置密码
    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    # 更改邮箱令牌
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})
    
    # 修改邮箱
    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    # 检查权限
    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    # 管理员权限
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    # 刷新用户最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)



# 匿名用户(未登录)
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    
    def is_administrator(self):
        return False



# 加载用户的回调函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    


# 将app全局的未登录current_app设置为AnonymousUser(可以统一使用can和is_administrator方法)
login_manager.anonymous_user = AnonymousUser

