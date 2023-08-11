from wtforms import Form, StringField, TextAreaField, SelectField, FileField
from wtforms import PasswordField, validators


class PostForm(Form):
    title = StringField('Заголовок статьи:')
    content = TextAreaField('Текст статьи:', render_kw={'rows': 15})
    category = SelectField('Категория:', choices=[])
    picture = FileField('Картинка для статьи')


class Registration(Form):
    """Форма для регистрации пользователя"""
    username = StringField('логин *', [validators.DataRequired()])
    first_name = StringField('Имя *', [validators.DataRequired()])
    last_name = StringField('Фамилия *', [validators.DataRequired()])
    phone = StringField('Контактный номер')
    email = StringField('Почта *', [validators.DataRequired()])
    password = PasswordField('Пароль *', [validators.Length(min=1, max=15),
                                          validators.EqualTo('confirm',
                                                             message='Пароли должны совпадать')])
    confirm = PasswordField('Подтверждения пароля *', [validators.DataRequired()])


class UserLogin(Form):
    """Форма для авторизации пользователя"""
    username = StringField('Логин')
    password = PasswordField('Пароль')


class UpdateUserProfile(Form):
    """Форма для редактирования профайла пользователя"""
    username = StringField('логин *', [validators.DataRequired()])
    first_name = StringField('Имя *', [validators.DataRequired()])
    last_name = StringField('Фамилия *', [validators.DataRequired()])
    phone = StringField('Контактный номер')
    email = StringField('Почта *', [validators.DataRequired()])
    bio = TextAreaField('БИО:', render_kw={'rows': 5})
    photo = FileField('Аватарка')