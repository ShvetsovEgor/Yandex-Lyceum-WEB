from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import SubmitField, FileField
from wtforms.validators import DataRequired


class GameAddForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    picture = FileField('Иллюстрация игры')
    genre = StringField('Жанр', validators=[DataRequired()])
    content = TextAreaField("Описание")
    archive = FileField('Файлы игры')
    platform = StringField('Поддерживаемые платформы', validators=[DataRequired()])
    created_date = StringField("Год релиза", validators=[DataRequired()])
    submit = SubmitField('Применить')
