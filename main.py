# импортируем библиотеки
from flask import Flask, render_template, redirect, make_response, jsonify, request, send_from_directory, send_file
from flask_login import LoginManager, logout_user, login_required, login_user, current_user
from flask_restful import Api
from data.users import User
from data.user_file import UserFile
from data import db_session
from forms.loginform import LoginForm
from forms.user import RegisterForm
import os
from waitress import serve
import shutil
import ssl
from hashlib import md5
from secret_key import flask_key

app = Flask(__name__)
app.config['SECRET_KEY'] = flask_key
api = Api(app)

certfile = 'ssl/certificate.crt'
keyfile = 'ssl/key.key'

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile, keyfile)

login_manager = LoginManager()
login_manager.init_app(app)


# Загрузчик пользователей
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


# Иконка сайта
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


# Иконка сайта для IOS
@app.route('/apple-touch-icon.png', methods=['GET'])
def apple_touch():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'apple-touch-icon.png', mimetype='image/png')


# Иконка сайта для IOS
@app.route('/apple-touch-icon-precomposed.png', methods=['GET'])
def apple_touch_p():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'apple-touch-icon-precomposed.png', mimetype='image/png')


# Файл для поисковых систем
@app.route('/robots.txt', methods=['GET'])
def robots():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'robots.txt')


# Карта сайта для поисковых систем
@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'sitemap.xml')


# Верификация сайта в google
@app.route('/google3f153d10dc591236.html', methods=['GET'])
def google():
    return render_template('google3f153d10dc591236.html')


# Верификация сайта в yandex
@app.route('/yandex_0cd3aba85eb52f46.html', methods=['GET'])
def yandex():
    return render_template('yandex_0cd3aba85eb52f46.html')


# страница с файлами
@app.route('/files')
@login_required
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        files = db_sess.query(UserFile).filter(UserFile.owner == current_user.id).all()
        if not os.path.isdir(os.path.join(os.getcwd(), f'files/id_user_{current_user.id}')):
            os.mkdir(os.path.join(os.getcwd(), f'files/id_user_{current_user.id}'))
    else:
        files = None
    return render_template("index.html", files=files)


# главная страница
@app.route('/')
@app.route('/index')
def files_page():
    if current_user.is_authenticated:
        return redirect("/files")
    else:
        return render_template('base.html')


# регистрация
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        shutil.copyfile('static/img/avatar/default_avatar.png', f'static/img/avatar/{user.id}.png')
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


# авторизация
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


# Выход из системы
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# профиль
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


# Загрузка файлов
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        user = current_user
        file = request.files['file']
        if file:
            # Вычисляем хэш загружаемого файла
            file_hash = md5(file.read()).hexdigest()

            # Проверяем, нет ли уже такого файла в базе данных
            existing_file = db_sess.query(UserFile).filter_by(hash=file_hash).first()
            if existing_file:
                return "Файл с таким содержимым уже загружен"

            # Сохраняем информацию о файле в базе данных
            db_file = UserFile()
            db_file.filename = file.filename
            db_file.owner = user.id
            db_file.directory = f"files/id_user_{user.id}/{file.filename}"
            db_file.hash = file_hash
            db_sess.add(db_file)
            db_sess.commit()

            # Сохраняем сам файл на сервере
            file.seek(0)  # Возвращаем указатель на начало файла
            file.save(f"files/id_user_{user.id}/{file.filename}")

            return redirect("/")
    return render_template('file_upload.html')


# скачивание файлов
@app.route('/download/<upload_id>')
@login_required
def download(upload_id):
    db_sess = db_session.create_session()
    file = db_sess.query(UserFile).filter_by(id=upload_id).first()
    user = current_user
    if current_user.id == file.owner == current_user.id:
        return send_file(f"files/id_user_{user.id}/{file.filename}", download_name=file.filename,
                         as_attachment=True)
    else:
        return


# удаление файлов
@app.route('/delete/<upload_id>')
@login_required
def delete(upload_id):
    db_sess = db_session.create_session()
    file = db_sess.query(UserFile).filter_by(id=upload_id).first()
    if current_user.id == file.owner == current_user.id:
        db_sess.delete(file)
        db_sess.commit()
        user = current_user
        try:
            os.remove(f"files/id_user_{user.id}/{file.filename}")
        except:
            pass
        return redirect("/")


# удаление аккаунта
@app.route('/delete_account')
@login_required
def delete_account():
    db_sess = db_session.create_session()
    user = db_sess.get(User, current_user.id)
    db_sess.delete(user)
    db_sess.commit()
    shutil.rmtree(f"files/id_user_{user.id}")
    return redirect("/")


# загрузка аватарки
@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if request.method == 'POST':
        file = request.files['file']
        os.remove(f'static/img/avatar/{current_user.id}.png')
        file.save(f'static/img/avatar/{current_user.id}.png')
    return redirect('/')


# изменение имени пользователя
@app.route('/change_username', methods=['GET', 'POST'])
@login_required
def change_username():
    if request.method == 'POST':
        new_name = request.form['new_username']
        db_sess = db_session.create_session()
        user_with_same_name = db_sess.query(User).filter(User.name == new_name).first()
        if user_with_same_name:
            return render_template('profile.html',
                                   message="Это имя пользователя уже занято. Пожалуйста, выберите другое.")
        else:
            user = db_sess.get(User, current_user.id)
            user.name = new_name
            db_sess.commit()
            return redirect('/')


# изменение пароля
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        db_sess = db_session.create_session()
        user = db_sess.get(User, current_user.id)
        user.set_password(new_password)
        db_sess.commit()
        return redirect('/')


# админ (пользователь)
@app.route('/admin')
@login_required
def admin_panel():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    if current_user.admin == 1 or current_user.owner == 1:
        return render_template('admin_panel.html', users=users)
    else:
        return redirect('/')


# вход под другим пользователем (для администраторов)
@login_required
def login_as(user_id):
    if current_user.admin == 1 or current_user.owner == 1:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        if user.admin == 1 or current_user.owner == 1:
            if current_user.owner == 1:
                login_user(user, True)
                return redirect('/')
            else:
                return redirect("/admin")
        else:
            login_user(user, True)
            return redirect('/')
    else:
        return redirect('/')


# добавление админа
@app.route('/set_admin/<user_id>')
@login_required
def set_admin(user_id):
    if current_user.owner == 1:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        user.admin = 1
        db_sess.commit()
        return redirect("/admin")
    else:
        return redirect('/admin')


# установить права пользователя
@app.route('/set_user/<user_id>')
@login_required
def set_user(user_id):
    if current_user.owner == 1:
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == user_id).first()
        user.admin = 0
        db_sess.commit()
        return redirect("/admin")
    else:
        return redirect('/admin')


# Ошибка 404
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': '404 Not Found'}), 404)


# Ошибка 400
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


# Запуск сайта
if __name__ == '__main__':
    db_session.global_init("db/database.db")
    serve(app, port=5000, host='127.0.0.1')
