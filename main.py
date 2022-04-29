from os import path
from urllib.parse import urlparse

import requests
from flask import Flask, render_template, redirect, request, abort, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_ngrok import run_with_ngrok

from bot import db
from config import API_TOKEN as token
from data import db_session
from data.comments import Comments
from data.games import Games
from data.users import User
from forms.comments import LeaveAComment
from forms.games import GameAddForm
from forms.user import AdminForm
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
run_with_ngrok(app)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/download/<filename>')
def download(filename):
    filepath = path.join(app.root_path, 'game_archives', filename)
    return send_file(filepath)


@app.route("/about_us")
def about_us():
    return render_template('about_us.html')


@app.route("/games/<name>", methods=['GET', 'POST'])
def game(name):
    db_sess = db_session.create_session()
    form = LeaveAComment()
    if request.method == 'GET':
        db_sess = db_session.create_session()

        try:
            game = db_sess.query(Games).filter(Games.title == name).one()
            comments = db_sess.query(Comments).filter(Comments.game_id == game.id).all()

            comments_lst = []
            for comment in comments:
                comments_lst += [[comment.content, db_sess.query(User).filter(User.id == int(comment.user_id)).one()]]
            return render_template("game.html", params=game, form=form, comments=comments_lst)
        except Exception as e:
            print(e)
            return abort(404)

    elif request.method == 'POST':
        try:
            db_sess = db_session.create_session()
            game = db_sess.query(Games).filter(Games.title == name).one()
            if form.is_submitted():

                if not current_user.is_authenticated:
                    return redirect("/register")
                comment = Comments()
                comment.user_id = current_user.id
                comment.game_id = game.id
                comment.content = form.content.data
                db_sess.add(comment)
                db_sess.commit()

            comments = db_sess.query(Comments).filter(Comments.game_id == game.id).all()
            comments_lst = []
            for comment in comments:
                comments_lst += [[comment.content, db_sess.query(User).filter(User.id == int(comment.user_id)).one()]]
            print(comments_lst)
            return render_template("game.html", params=game, form=form, comments=comments_lst)
        except Exception as e:
            print(e)
            return abort(404)


# Ошибка клиента (400-499).
# Ошибка сервера (500-510).
# Источник: https://allerrorcodes.ru/http-2
for error in range(400, 511):
    try:
        @app.errorhandler(error)
        def any_error(error):
            with open('static/img/mistake.jpg', 'wb') as file:
                file.write(requests.get(f'https://http.cat/{error.code}').content)
            return render_template('error.html')
    except Exception as e:
        print(f"Не удалось подключить к обработчику ошибку {error}")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        games = db_sess.query(Games).all()
    else:
        games = db_sess.query(Games).all()
    print(games)
    games_slider = games[:6]
    print(games_slider)
    return render_template("index.html", games=games, games_slider=games_slider)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if form.role.data == 'Подписчик':
            user_type = 3
        elif form.role.data == 'Разработчик':
            user_type = 2
        user = User(
            name=form.name.data,
            email=form.email.data,
            type_of_user=user_type
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    form = AdminForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        print(user)
        if user is None:
            return render_template('admin.html', title='Добавление админа',
                                   form=form,
                                   message="Такого пользователя не существует")
        if user.name != form.name.data:
            return render_template('admin.html', title='Добавление админа',
                                   form=form,
                                   message="У этого пользоваеля другое имя")
        user.type_of_user = 1
        db_sess.commit()
        return redirect('/')
    return render_template('admin.html', title='Добавление админа', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/game_add', methods=['GET', 'POST'])
@login_required
def add_games():
    form = GameAddForm()
    if request.method == 'GET':
        return render_template('games.html', title='Добавление игры',
                               form=form)
    elif request.method == 'POST':
        if form.is_submitted():
            db_sess = db_session.create_session()
            game = Games()
            game.title = form.title.data
            game.content = form.content.data
            game.picture = form.picture.data.filename
            game.archive = form.archive.data.filename
            game.genre = form.genre.data
            game.platform = form.platform.data
            game.created_date = form.created_date.data
            current_user.games.append(game)
            db_sess.merge(current_user)
            db_sess.commit()
            o = urlparse(request.base_url)
            game_link = f"http://{o.netloc}/games/{game.title}"
            all = db.get_subscriptions()
            print(all)
            for i in range(len(all)):
                id = all[i][0]
                text = f'Привет, вышла новая видеоигра "{game.title}" в жанре {game.genre}, почему бы не скачать? ' \
                       f'Держи ссылку {game_link}'
                response = requests.get(f'https://api.telegram.org/bot{token}/sendMessage?chat_id={id}&text={text}')
            photo = request.files['picture']
            archive = request.files['archive']
            if form.picture.data.filename:
                with open(f"static/img/{form.picture.data.filename}", 'wb') as file:
                    file.write(photo.read())
            if form.archive.data.filename:
                with open(f"game_archives/{form.archive.data.filename}", 'wb') as file:
                    file.write(archive.read())
            return redirect('/')
        else:
            print("NO SUBMIT")


@app.route('/games/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_games(id):
    form = GameAddForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        game = db_sess.query(Games).filter(Games.id == id).first()
        if game:
            form.title.data = game.title
            form.content.data = game.content
            # form.picture.label = game.picture
            # form.archive.data.filename = game.archive
            form.genre.data = game.genre
            form.platform.data = game.platform
            form.created_date.data = game.created_date
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        game = db_sess.query(Games).filter(Games.id == id).first()
        if game:
            game.title = form.title.data
            game.content = form.content.data
            game.genre = form.genre.data
            game.platform = form.platform.data
            game.created_date = form.created_date.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('games.html',
                           title='Редактирование игры',
                           form=form
                           )


@app.route('/games_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def games_delete(id):
    db_sess = db_session.create_session()
    games = db_sess.query(Games).filter(Games.id == id).first()
    if games:
        db_sess.delete(games)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


def main():
    db_session.global_init("db/digitalmarket.db")
    app.run()


if __name__ == '__main__':
    main()
