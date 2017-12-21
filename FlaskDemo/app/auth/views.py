from flask import render_template, session, redirect, request, url_for, flash
from . import auth
from .forms import LoginForm, RegisterForm
from flask_login import login_required, login_user, logout_user
from ..models import User, Role
from .. import db
from flask_login import current_user
from ..email import send_email_cloud

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
            and request.endpoint \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The configuration link is invalid or has expired')

    return redirect(url_for('main.index'))

@auth.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        userobj = User.query.filter_by(email=form.email.data).first()
        if userobj is not None and userobj.verify_password(form.password.data) == True:
            login_user(userobj, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password!')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/secret', methods=['GET', 'POST'])
@login_required
def secret():
    return 'Only authenticated users are allowed!'

@auth.route('/register', methods=['GET', 'POST'])
def register():
    regform = RegisterForm()
    if regform.validate_on_submit():
        user_new = User(username=regform.username.data, email=regform.email.data,
                        password=regform.password.data)
        db.session.add(user_new)
        db.session.commit()
        token = user_new.generate_confirmation_token()
        send_email_cloud(user_new.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user_new, token=token)
        flash('A confirmation email has been sent to you by email!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=regform)

@auth.route('/index')
def index():
    name = session.get('name')
    return render_template('auth/index.html', name=name)


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email_cloud(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A confirmation email has been sent to you by email!')
    return redirect(url_for('main.index'))