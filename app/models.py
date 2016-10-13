# -*- coding:utf-8 -*-

'''
数据库表
'''


from . import db
from . import login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin

from markdown import markdown
import bleach

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request, url_for
from . import db

from datetime import datetime
import hashlib

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


# 关注
class Follow(db.Model):

    __tablename__ = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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
    
    # email hash
    avatar_hash = db.Column(db.String(32))
    
    # Post中author是一个user
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    
    # 一对多关系(关注了哪些人)
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id], 
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')       # 父表和子表的同步关系
    # 一对多关系(被哪些人关注)
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], 
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                               cascade='all, delete-orphan')
    
    # 评论是一对多
    comments = db.relationship('Comment', backref='author', lazy='dynamic')


    def __repr__(self):
        return '<User %r>' % self.username
 
    
    # 模型初始化工作
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:                       # 赋予用户角色
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        
        # 缓存email hash
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        
        # 默认关注自己
        self.followed.append(Follow(followed=self))
    
    
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
        self.email = new_email  # 变更邮箱
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()  # 变更email hash
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


    # 生成头像url
    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        email_hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{email_hash}?s={size}&d={default}&r={rating}'.format(url=url, email_hash=email_hash, size=size, default=default, rating=rating)
    
    
    '''关注关系的辅助方法'''
    # 关注
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    # 取消关注
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    # 查询是否正在关注
    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    # 查询是否被关注
    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None
    
    # 获取所关注用户的文章
    @property
    def followed_posts(self):
        return Post.query.join(     # 使用联合查询
                Follow, Follow.followed_id== Post.author_id).filter(    # 在Post表和Follow表中查询followed_id和author_id对应的rows
                        Follow.follower_id == self.id)                  # follower_id为self.id

    # 关注自己
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()


    # 生成虚拟数据(开发测试)
    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     realname=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except:
                db.session.rollback()


# 发表文章
class Post(db.Model):

    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True);
    body = db.Column(db.Text)                       # 存放的MarkDown纯文本
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    body_html = db.Column(db.Text)                  # 存放MarkDown文本对应的HTML格式
    
    # 文章和评论是一对多关系
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    # 生成虚拟数据
    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count-1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                     timestamp=forgery_py.date.date(True),
                     author=u)
            db.session.add(p)
            db.session.commit()
    
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):        # 监听body字段, 如果body字段更新, 函数自动被调用
        # 允许存在的html标签
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'h1', 
                        'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean( # 清除所有允许存在的tags # linkify将纯文本的url生成连接
            markdown(value, output_format='html'),      # markdown函数将(表单提交的)Markdown文本转换成HTML
            tags=allowed_tags, strip=True))



# 发表评论
class Comment(db.Model):
    
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)    # 是否显示评论
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
    


# 注册Post和Comment类body字段的监听函数
db.event.listen(Post.body, 'set', Post.on_changed_body)
db.event.listen(Comment.body, 'set', Comment.on_changed_body)



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

