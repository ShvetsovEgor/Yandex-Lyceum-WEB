from flask import Flask, render_template, redirect, request, abort, make_response, url_for
from data import db_session
from data.users import User
from data.games import Games
from forms.user import RegisterForm, LoginForm
from forms.news import NewsForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

#
# @app.errorhandler(500)
# def internal_error(error):
#     return requests.get(f'https://http.cat/500').content
#
#
# @app.errorhandler(404)
# def not_found(error):
#     return requests.get(f'https://http.cat/500').content


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        games = db_sess.query(Games)
    else:
        games = db_sess.query(Games)
    return render_template("index.html", games=games)


@app.route("/games/<name>")
def game(name):
    db_sess = db_session.create_session()
    a = db_sess.query(Games).filter(Games.title == name).all()
    a = list(a)
    print(a)
    print(a[0].genre)
    # нужно заполнить params
    return render_template("game.html", params=a[0])


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
        user = User(
            name=form.name.data,
            email=form.email.data,
            type_of_user=1
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


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


@app.route('/games', methods=['GET', 'POST'])
@login_required
def add_games():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        games = Games()
        games.title = form.title.data
        games.content = form.content.data
        current_user.games.append(games)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('games.html', title='Добавление новости',
                           form=form)


@app.route('/games/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_games(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        games = db_sess.query(Games).filter(Games.id == id,
                                            Games.user == current_user
                                            ).first()
        if games:
            form.title.data = games.title
            form.content.data = games.content
            form.is_private.data = games.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        games = db_sess.query(Games).filter(Games.id == id,
                                            Games.user == current_user
                                            ).first()
        if games:
            games.title = form.title.data
            games.content = form.content.data
            games.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('games.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/games_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def games_delete(id):
    db_sess = db_session.create_session()
    games = db_sess.query(Games).filter(Games.id == id,
                                        Games.user == current_user
                                        ).first()
    if games:
        db_sess.delete(games)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


def Redirect_to_game(location):
    print(111111111)
    # return redirect(location, code=302, Response=None)


def main():
    db_session.global_init("db/digitalmarket.db")
    app.run()


if __name__ == '__main__':
    main()
