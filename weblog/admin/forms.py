from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms import IntegerField, TextAreaField, SelectField, RadioField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from flask_pagedown.fields import PageDownField
from flask_login import current_user

from ..models import db, User, Role
from ..email import send_email
from ..user.forms import ProfileForm


class AdminProfileForm(ProfileForm):
    '''管理员编辑用户个人信息所用的表单类'''

    name = StringField('用户名', validators=[DataRequired(), Length(2, 22),
            Regexp('^\w+$', 0, '用户名只能使用单词字符')])
    age = IntegerField('年龄')
    gender = RadioField('性别', choices=[('Male', '男'), ('Female', '女')])
    phone_number = StringField('电话', validators=[Length(6, 16)])
    location = StringField('所在城市', validators=[Length(2, 16)])
    about_me = TextAreaField('个人简介')
    # 这个选择框，选择的结果就是 int 数值，也就是用户的 role_id 属性值
    # 参数 coerce 规定选择结果的数据类型
    # 该选择框须定义 choices 属性，也就是选项列表
    # 每个选项是一个元组，包括 int 数值（页面不可见）和选项名（页面可见）
    # 选择某个选项，等号前面的变量 role_id 就等于对应的 int 数值
    role_id = SelectField('角色', coerce=int)
    confirmed = BooleanField('已通过邮箱验证')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kw):
        super().__init__(user, *args, **kw)
        # 初始化表单类实例时，需要定义好 SelectField 所需的选项列表
        self.role_id.choices = [(role.id, role.name)
                for role in Role.query.order_by(Role.permissions)]
