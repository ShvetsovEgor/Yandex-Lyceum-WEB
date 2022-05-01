from wtforms import TextAreaField
from wtforms import SubmitField

from flask_wtf import FlaskForm

class LeaveAComment(FlaskForm):
    content = TextAreaField("Текст комментария")
    submit = SubmitField('Оставить комментарий')
