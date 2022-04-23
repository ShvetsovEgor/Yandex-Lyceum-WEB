import requests
from flask import Flask, render_template, redirect, request, abort, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from os import path
from data import db_session
from data.games import Games
from data.users import User
from forms.news import GameAddForm
from forms.user import AdminForm
from forms.user import RegisterForm, LoginForm
from flask_ngrok import run_with_ngrok
import config
import logging
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from sqlighter import SQLighter

# задаем уровень логов
logging.basicConfig(level=logging.INFO)

# инициализируем бота
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)

# инициализируем соединение с БД
db = SQLighter('db.db')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
run_with_ngrok(app)

login_manager = LoginManager()
login_manager.init_app(app)


# бот начало
# Команда активации подписки
@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его
        db.add_subscriber(message.from_user.id)
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, True)

    await message.answer(
        "Вы успешно подписались на рассылку!\nЖдите, скоро выйдут новые обзоры и вы узнаете о них первыми =)")


# Команда отписки
@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if (not db.subscriber_exists(message.from_user.id)):
        # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
        db.add_subscriber(message.from_user.id, False)
        await message.answer("Вы итак не подписаны.")
    else:
        # если он уже есть, то просто обновляем ему статус подписки
        db.update_subscription(message.from_user.id, False)
        await message.answer("Вы успешно отписаны от рассылки.")


# бот конец(почти)
@app.route('/download/<filename>')
def download(filename):
    filepath = path.join(app.root_path, 'game_archives', filename)
    print(filepath)
    return send_file(filepath)


@app.route("/about_us")
def about_us():
    return render_template('about_us.html')


@app.route("/games/<name>")
def game(name):
    db_sess = db_session.create_session()
    game = db_sess.query(Games).filter(Games.title == name).one()
    return render_template("game.html", params=game)


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
        print(error)


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
    return render_template("index.html", games=games)


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


@app.route('/games', methods=['GET', 'POST'])
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

            # проверяем наличие новых игр и делаем рассылки
            async def scheduled(wait_for):
                subscriptions = db.get_subscriptions()
                for s in subscriptions:
                    await bot.send_photo(
                        s[1],
                        game.picture,
                        caption=game.title + "\n"  + "\n" + game.genre + "\n\n" + game.content,
                        disable_notification=True
                    )

            photo = request.files['picture']
            archive = request.files['archive']
            with open(f"static/img/{form.picture.data.filename}", 'wb') as file:
                file.write(photo.read())
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
        game = db_sess.query(Games).filter(Games.id == id,
                                           Games.user == current_user
                                           ).first()
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
        game = db_sess.query(Games).filter(Games.id == id,
                                           Games.user == current_user
                                           ).first()
        if game:
            game.title = form.title.data
            game.content = form.content.data
            # game.picture = form.picture.data.filename
            # game.archive = form.archive.data.filename
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
    games = db_sess.query(Games).filter(Games.id == id,
                                        Games.user == current_user
                                        ).first()
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
