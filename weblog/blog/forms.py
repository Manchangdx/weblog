from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    '''评论表单类'''

    body = TextAreaField('', validators=[DataRequired()])
    submit = SubmitField('提交')
