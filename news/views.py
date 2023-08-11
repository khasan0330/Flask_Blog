import os
import uuid as uuid

from flask import render_template, request, abort, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from news.forms import Registration
from news.models import Users
from news import db, app
from news.forms import PostForm
from news.models import Post, Category
from news.forms import UserLogin, UpdateUserProfile

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_login'


@login_manager.user_loader
def load_user(user_id):
    """Чеккер пользователя, по документации"""
    return Users.query.get(int(user_id))


@app.route('/')
def index():
    posts = Post.query.all()
    categories = Category.query.all()
    return render_template('news/index.html',
                           title='Главная',
                           categories=categories,
                           posts=posts
                           )


@app.route('/category/<int:id>')
def category_list(id: int):
    """Реакция на нажатия кнопок категорий"""
    categories = Category.query.all()
    posts = Post.query.filter(Post.category_id == id)
    current = Category.query.get(id)
    return render_template('news/index.html',
                           title=current,
                           categories=categories,
                           posts=posts,
                           current=current)


@app.route('/post/<int:id>')
def post_detail(id):
    """Статья на отдельной странице"""
    post = Post.query.filter(Post.id == id).first()
    return render_template('news/post_detail.html', post=post)


@app.route('/search/', methods=['GET'])
def search_result():
    """ДЛя поиска"""
    q = request.args.get('q')
    categories = Category.query.all()
    search = Post.title.contains(q) | Post.content.contains(q)
    posts = Post.query.filter(search).all()
    if not posts:
        abort(404)
    return render_template('news/index.html',
                           categories=categories,
                           posts=posts)


@app.route('/post/create', methods=['POST', 'GET'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        category = request.form['category']
        category_id = Category.query.filter(Category.title == category).first().id
        picture_file = request.files['picture']
        picture_name = secure_filename(picture_file.filename)
        picture_name = str(uuid.uuid1()) + '_' + picture_name
        picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], picture_name))
        post = Post(title=title,
                    content=content,
                    category_id=category_id,
                    picture=picture_name,
                    author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('category_list', id=category_id))

    categories = Category.query.all()
    form = PostForm()
    form.category.choices = [cat.title for cat in categories]
    return render_template('news/create_post.html', form=form)


@app.errorhandler(404)
def page404(e):
    return render_template('news/404.html'), 404


@app.route('/post/<int:id>/delete/')
def delete_post(id: int):
    """Удаление поста"""
    post = Post.query.get(id)
    category = post.category_id
    db.session.delete(post)
    db.session.commit()
    flash(f"Вы удалили пост {post.title}")
    return redirect(url_for('category_list', id=category))


@app.route('/post/<int:id>/update/', methods=['POST', 'GET'])
def update_post(id: int):
    """Редактирование поста"""
    post = Post.query.get(id)
    categories = Category.query.all()
    if request.method == 'POST':
        category = request.form['category']
        category_id = Category.query.filter(Category.title == category).first().id
        post.category_id = category_id
        post.title = request.form['title']
        post.content = request.form['content']
        if picture_file := request.files['picture']:
            picture_name = secure_filename(picture_file.filename)
            picture_name = str(uuid.uuid1()) + '_' + picture_name
            picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], picture_name))
            post.picture = picture_name

        db.session.add(post)
        db.session.commit()
        return redirect(url_for('post_detail', id=id))

    form = PostForm(obj=post)
    form.category.choices = [cat.title for cat in categories]
    return render_template('news/create_post.html', form=form, id=id)


@app.route('/registration', methods=['POST', 'GET'])
def user_registration():
    """Логика для регистрации"""
    form = Registration(request.form)
    if request.method == 'POST' and form.validate():
        password_hash = generate_password_hash(form.password.data, method='scrypt')
        user = Users(first_name=form.first_name.data,
                     last_name=form.last_name.data,
                     username=form.username.data,
                     phone=form.phone.data,
                     email=form.email.data,
                     password=password_hash
                     )
        try:
            db.session.add(user)
            db.session.commit()
            flash("Аккаунт создан успешно, пожалуйста войдите")
            return redirect(url_for('user_login'))
        except IntegrityError:
            db.session.rollback()
            flash("Пользователь с такими данными существует", 'error')

    return render_template('news/user_registration.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    """Авторизация пользователя"""
    form = UserLogin(request.form)
    if request.method == 'POST':
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Вы успешно вошли в систему")
            return redirect(url_for('index'))
        else:
            flash("Не правильный логин или пароль", 'error')

    return render_template('news/user_login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/<int:id>')
def user_profile(id: int):
    """Профайл пользователя"""
    user = Users.query.get(id)
    return render_template('news/user_profile.html', user=user)


@app.route('/profile/<int:id>/update/', methods=['POST', 'GET'])
@login_required
def update_user(id: int):
    """Логика для редактирования пользователя"""
    user = Users.query.get(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.phone = request.form['phone']
        user.email = request.form['email']
        user.bio = request.form['bio']
        if picture_file := request.files['photo']:
            picture_name = secure_filename(picture_file.filename)
            picture_name = str(uuid.uuid1()) + '_' + picture_name
            picture_file.save(os.path.join(app.config['UPLOAD_FOLDER'], picture_name))
            user.photo = picture_name
        try:
            db.session.add(user)
            db.session.commit()
            flash("Отредактировано успешно")
            return redirect(url_for('user_profile', id=id))
        except IntegrityError:
            db.session.rollback()
            flash("Пользователь с такими данными существует", 'error')
    elif str(current_user) != user.username:
        abort(404)

    form = UpdateUserProfile(obj=user)
    return render_template('news/edit_user_profile.html', form=form, id=id)


@app.route('/profile/<int:id>/delete/')
@login_required
def delete_user(id: int):
    """Удаление пользователя"""
    user = Users.query.get(id)
    if str(current_user) != user.username:
        abort(404)
    db.session.delete(user)
    db.session.commit()
    flash("Аккаунт удалён")
    return redirect(url_for('index'))


# Utils
@app.template_filter('time_filter')
def jinja2_filter_datetime(date):
    format = "%d.%m.%Y %H:%M:%S"
    return date.strftime(format)
