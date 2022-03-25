from flask import Blueprint, request, jsonify, render_template, url_for, flash, redirect
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash

from src.database import Admin, User
from src.forms import LoginForm

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
# from src.database import User, db, SensorData, Device, MainSensor, Admin

admin = Blueprint("admin", __name__)


@admin.get('/')
@login_required
def admin_index():
    if current_user.is_authenticated:
        return redirect('/home')
    else:
        return redirect('/login')


@admin.get('/home')
@login_required
def admin_home():
    return render_template('admin_home.html', title='DashBoard', active='dashboard')


@admin.route('/login', methods=['POST', 'GET'])
def admin_login():
    form = LoginForm()
    if form.validate_on_submit():

        admin = Admin.query.filter_by(email=form.email.data).first()

        if admin and check_password_hash(admin.password, form.password.data):
            login_user(admin)
            return redirect(url_for('admin.admin_home'))
        else:
            flash("Login Unsuccessful.Please check email and password", 'danger')

        # flash("Login Unsuccessful.Please check email and password", 'danger')
    return render_template('login.html', form=form)


@admin.route('/logout')
def admin_logout():
    logout_user()
    return redirect('/login')


@admin.route('/users')
@login_required
def admin_users():
    users = User.query.all()
    return render_template('users.html', title='users', active='users', users=users)


@admin.route('/settings')
@login_required
def admin_settings():
    return render_template('settings.html', title='settings', active='users')