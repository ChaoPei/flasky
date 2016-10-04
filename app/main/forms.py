# -*- coding:utf-8 -*-

'''
表单类型定义
'''


from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Required


# post名字单元
class NameForm(Form):
    
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')
