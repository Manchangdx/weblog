from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms import IntegerField, TextAreaField, SelectField, RadioField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from flask_login import current_user

from ..models import User, Role


class ProfileForm(FlaskForm):
    '''用户编辑个人信息所用的表单类'''

    name = StringField('用户名', validators=[DataRequired(), Length(2, 22),
            Regexp('^\w+$', 0, '用户名只能使用单词字符')])
    age = IntegerField('年龄')
    gender = RadioField('性别', choices=[('Male', '男'), ('Female', '女')])
    phone_number = StringField('电话', validators=[Length(6, 16)])
    location = StringField('所在城市', validators=[Length(2, 16)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kw):
        '''创建该类实例时，需要提供一个用户对象作为参数'''
        # 基类 FlaskForm 有 __init__ 方法，这里需要 super 方法执行基类的同名方法
        super().__init__(*args, **kw)
        # 需要提供被修改的用户实例作为参数，自定义表单验证器要用
        self.user = user

    def validate_name(self, field):
        if (field.data != self.user.name and 
                User.query.filter_by(name=field.data).first()):
            raise ValidationError('该用户名已经存在')

    def validate_phone_number(self, field):
        if (field.data != self.phone_number.data and 
                User.query.filter_by(phone_number=field.data).first()):
            raise ValidationError('该电话号码已经存在')


class ChangePasswordForm(FlaskForm):
    '''用户登录后修改密码所使用的表单类'''

    old_password = PasswordField('原密码', validators=[DataRequired()])
    password = PasswordField('新密码', 
            validators=[DataRequired(), Length(3, 22)])
    repeat_password = PasswordField('重复新密码',
            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('提交')

    def validate_old_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('原密码错误')

    def validate_password(self, field):
        if not field.data.replace('_', '').isalnum():
            raise ValidationError('密码只能由数字、字母和下划线组成')
        if field.data.isnumeric() or field.data.isalpha():
            raise ValidationError('密码必须同时包含数字和字母')


class BeforeResetPasswordForm(FlaskForm):
    '''忘记密码时利用邮箱重置密码前所使用的【邮箱】表单类'''

    email = StringField('邮箱', validators=[DataRequired(), Email()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱未注册')


class ResetPasswordForm(FlaskForm):
    '''忘记密码时利用邮箱重置密码时所使用的【密码】表单类'''

    password = PasswordField('新密码', 
            validators=[DataRequired(), Length(3, 22)])
    repeat_password = PasswordField('重复新密码',
            validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('提交')

    def validate_password(self, field):
        if not field.data.replace('_', '').isalnum():
            raise ValidationError('密码只能由数字、字母和下划线组成')
        if field.data.isnumeric() or field.data.isalpha():
            raise ValidationError('密码必须同时包含数字和字母')


class ChangeEmailForm(FlaskForm):
    '''变更邮箱的表单类'''

    email = StringField('新邮箱', validators=[DataRequired(), Email()])
    repeat_email = StringField('重复新邮箱', 
            validators=[DataRequired(), EqualTo('email')])
    password = PasswordField('密码', validators=[DataRequired()])
    submit = SubmitField('提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已经被注册')

    def validate_password(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('密码错误')
