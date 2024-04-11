import shutil

from flask import Flask, render_template, redirect, make_response, jsonify, request, send_from_directory, send_file
from flask_login import LoginManager, logout_user, login_required, login_user, current_user, AnonymousUserMixin
from flask_restful import Api
from data.users import User
from data.user_file import UserFile
from data import db_session
from forms.loginform import LoginForm
from forms.user import RegisterForm
from io import BytesIO
import aspose.words as aw
import os
from file_upload import Upload

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
@app.route('/index')
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        print(1)
        files = db_sess.query(UserFile).filter(UserFile.owner == current_user.id).all()
        print(current_user.id)
        if not os.path.isdir(f"{os.getcwd()}/static/files/id_user_{current_user.id}"):
            os.mkdir(f"{os.getcwd()}/static/files/id_user_{current_user.id}")
    else:
        files = None
    print()
    return render_template("index.html", files=files)


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
            email=form.email.data
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


@app.route('/update_user')
def update_user():
    db_sess = db_session.create_session()
    user = db_sess.query(User).first()
    if user:
        user.name = "Пользователь 2"
        db_sess.commit()
    return user.name


@app.route('/new_user')
def new_user():
    db_sess = db_session.create_session()
    user = db_sess.query(User).first()
    if not user:
        user = User()
        user.name = "Пользователь 1"
        user.email = "email@email.ru"
        db_sess.add(user)
        db_sess.commit()
    print(user.name)
    return user.name


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        user = current_user
        file = request.files['file']
        db_file = UserFile()
        db_file.filename = file.filename
        db_file.owner = user.id
        db_file.directory = f"static/files/id_user_{user.id}/{file.filename}"
        db_sess.add(db_file)
        db_sess.commit()
        file.save(f"static/files/id_user_{user.id}/{file.filename}")
        return redirect("/")
    return render_template('file_upload.html')


# конвертация файлов разных форматов

@app.route('/conversion/<upload_id>')
@login_required
def conversion(upload_id):
    print(upload_id)
    db_sess = db_session.create_session()
    file = db_sess.query(UserFile).filter_by(id=upload_id).first()
    if current_user.id == file.owner == current_user.id:
        user = current_user
        # из txt в pdf
        doc = aw.Document(f"static/files/id_user_{user.id}/{file.filename}")
        doc.save(f"static/files/id_user_{user.id}/{''.join(file.filename.split('.')[:-1])}.pdf")
        db_sess = db_session.create_session()
        user = current_user
        db_file = UserFile()
        db_file.filename = f"{''.join(file.filename.split('.')[:-1])}.pdf"
        db_file.owner = user.id
        db_file.directory = f"static/files/id_user_{user.id}/{''.join(file.filename.split('.')[:-1])}.pdf"
        db_sess.add(db_file)
        db_sess.commit()
        return redirect("/")


# create download function for download files
@app.route('/download/<upload_id>')
@login_required
def download(upload_id):
    db_sess = db_session.create_session()
    file = db_sess.query(UserFile).filter_by(id=upload_id).first()
    user = current_user
    if current_user.id == file.owner == current_user.id:
        return send_file(f"static/files/id_user_{user.id}/{file.filename}", download_name=file.filename, as_attachment=True)
    else:
        return


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
            os.remove(f"static/files/id_user_{user.id}/{file.filename}")
        except:
            pass
        return redirect("/")


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': error}), 404)


@app.errorhandler(400)
def bad_request(_):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    db_session.global_init("db/database.db")
    app.run(port=8080, host='127.0.0.1')
