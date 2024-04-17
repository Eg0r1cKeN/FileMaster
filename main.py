from flask import Flask, render_template, redirect, make_response, jsonify, request, send_from_directory, send_file
from flask_login import LoginManager, logout_user, login_required, login_user, current_user, AnonymousUserMixin
from flask_restful import Api
from data.users import User
from data.user_file import UserFile
from data import db_session
from forms.loginform import LoginForm
from forms.user import RegisterForm
import os
from waitress import serve
import shutil

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
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


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


@app.route('/')
@app.route('/index')
def files_page():
    if current_user.is_authenticated:
        return redirect("/files")
    else:
        return render_template('base.html')


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
        shutil.copyfile('static/img/avatar/default_avatar.png', f'files/avatar/{current_user.id}.png')
        return redirect('/files')
    return render_template('register.html', title='Регистрация', form=form)


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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


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
        db_file.directory = f"files/id_user_{user.id}/{file.filename}"
        db_sess.add(db_file)
        db_sess.commit()
        file.save(f"files/id_user_{user.id}/{file.filename}")
        return redirect("/")
    return render_template('file_upload.html')


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


@app.route('/delete_account')
@login_required
def delete_account():
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(current_user.id)
    db_sess.delete(user)
    db_sess.commit()
    shutil.rmtree(f"files/id_user_{user.id}")
    return redirect("/")


@app.route('/upload_avatar', methods=['GET', 'POST'])
@login_required
def upload_avatar():
    if request.method == 'POST':
        file = request.files['file']
        os.remove(f'static/img/avatar/{current_user.id}.png')
        file.save(f'static/img/avatar/{current_user.id}.png')
    return redirect('/')



@app.errorhandler(404)
def not_found():
    return make_response(jsonify({'error': '404 Not Found'}), 404)


@app.errorhandler(400)
def bad_request():
    return make_response(jsonify({'error': 'Bad Request'}), 400)


if __name__ == '__main__':
    db_session.global_init("db/database.db")
    serve(app, port=80, host='127.0.0.1')
