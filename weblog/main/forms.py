from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from flask_pagedown.fields import PageDownField

from ..models import db, User
from ..email import send_email


class RegisterForm(FlaskForm):
    '''注册表单类'''

    name = StringField('名字', validators=[DataRequired(), Length(3, 22),
            # Regexp 接收三个参数，分别为正则表达式、flags 、提示信息
            # flags 也叫作「旗标」，没有的话写为 0
            Regexp('^\w+$', 0, 'User name must have only letters.')])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired(),
            Length(3, 32)])
    repeat_password = PasswordField('重复密码', validators=[
            DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email already registered.')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('This name already registered.')

    def validate_password(self, field):
        if not field.data.replace('_', '').isalnum():
            raise ValidationError('密码只能由数字、字母和下划线组成')
        if field.data.isnumeric() or field.data.isalpha():
            raise ValidationError('密码必须同时包含数字和字母')

    def create_user(self):
        '''创建新用户并存入数据库，发送验证邮件'''
        user = User()
        self.populate_obj(user)
        user.avatar_hash = user.gravatar()
        db.session.add(user)
        db.session.commit()
        # 使用令牌生成器生成 token ，将其作为邮件中验证链接的一部分
        # 新用户注册后收到验证邮件，点击邮件中的验证链接
        # 视图函数 main.confirm_user 会调用 user.confirm_user 方法
        # 该方法使用令牌生成器的 loads 验证 token
        token = user.generate_confirm_user_token()
        send_email(user, user.email, 'confirm_user', token)
        return user


class LoginForm(FlaskForm):
    '''登录表单类'''

    email = StringField('邮箱', validators=[DataRequired(), Length(6, 64),
            Email()])
    password = PasswordField('密码', validators=[DataRequired(),
            Length(3, 32)])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱未注册')

    def validate_password(self, field):
        user = User.query.filter_by(email=self.email.data).first()
        if user and not user.verify_password(field.data):
            raise ValidationError('密码输入错误')


class BlogForm(FlaskForm):
    '''博客表单类'''

    # 这里使用 Flask-PageDown 提供的字段类，以支持 Markdown 编辑
    # 前端再设置一下预览，就可以在输入框输入 Markdown 语句并显示在页面上
    body = PageDownField('记录你的想法：', validators=[DataRequired()])
    submit = SubmitField('发布')
