from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.orm import query
from corporation import db, bcrypt, discord, scheduler
from corporation.models import User, Post, Role, Rolevsuser, Tribute, Division
from corporation.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm, inf_Form, Divisions_weight
from corporation.users.utils import save_picture, send_reset_email, send_confirmation_email
from flask_discord import requires_authorization
from corporation.data.scraping import RSI_account
from sqlalchemy import func


from flask import Blueprint

users = Blueprint('users', __name__)


@users.route("/user/update", methods=['GET', 'POST'])
@login_required
def update_RSI_info():

    current_user.update_info()

    return redirect(url_for('users.account'))


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        RSI_info = RSI_account(RSI_handle=form.RSI_handle.data)
        user = user = User.query.filter(func.lower(User.RSI_handle) == func.lower(RSI_info.RSI_handle)).first()
        if user:
            user.RSI_moniker=RSI_info.Moniker
            user.image_file=RSI_info.image_link
            user.RSI_number=RSI_info.citizen
            user.email=form.email.data
            user.password=hashed_password
            user.registered = True
        else:
            user = User(RSI_handle=RSI_info.RSI_handle, RSI_moniker=RSI_info.Moniker, image_file=RSI_info.image_link,
                    RSI_number=RSI_info.citizen, email=form.email.data, password=hashed_password, registered=True)
            db.session.add(user)
            
        db.session.commit()
        send_confirmation_email(user)

        role = Role.query.filter_by(title="Corporateer").first()
        user.update_info()

        flash(f'Your account has been created! Please look for a confirmation email.', 'success')
        return redirect(url_for('users.login'))
    return render_template("user/register.html", title="Register", form=form)


@users.route("/discord/<int:type>")
def discord_login(type):
    if current_user.is_authenticated and type == 1:
        logout_user()
        return redirect(url_for('main.home'))

    return discord.create_session()


@users.route("/discord_callback")
def callback():
    
    if current_user.is_authenticated:
        discord.callback()
        user = discord.fetch_user()
        user_account = User.query.filter_by(RSI_handle=current_user.RSI_handle).first()
        user_account.discord_id = user.id
        user_account.discord_username = user.username+'#' + user.discriminator

        if user.is_owner():
            user_account.security = 5

        db.session.commit()
        discord.revoke()
        return redirect(url_for('users.account'))

    try:
        discord.callback()
        user = discord.fetch_user()
        user_account = User.query.filter_by(discord_id=user.id).first()
    except:
        return redirect(url_for("users.login"))

    if user_account:
        user_account.discord_username = user.username+'#' + user.discriminator
        db.session.commit()
        discord.revoke()
        login_user(user_account, remember=False)
        return redirect(url_for('users.account'))

    else:
        discord.revoke()
        return redirect(url_for('users.register'))



@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(func.lower( User.RSI_handle) == func.lower(form.RSI_handle.data)).first()
        

        if user and user.test_password(password=form.password.data):
            user.update_info()
            
            if user.email_confirmed == False:
                send_confirmation_email(user)
                flash(
                    'Login Unsuccessful. Please check your email for verification', 'danger')
                return redirect(url_for('users.login'))

            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('users.account'))
        else:
            flash('Login Unsuccessful. Please check RSI handle and password', 'danger')
    return render_template("user/login.html", title="Login", form=form)


@users.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

#=======================================================================================
@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    
    return render_template("user/account.html", title="Account")

@users.route("/account/update_weight", methods=['GET', 'POST'])
@login_required
def weight_form_submition():
    
    weight_form = Divisions_weight(prefix = "weight")
    if weight_form.validate_on_submit():
        for weight in weight_form.weights:
            role = Role.query.filter_by(division_id= weight.division.data, div_member= True).first()
            link = Rolevsuser.query.filter_by(user_id = current_user.id , role_id = role.id).first()
            link.weight = weight.weight.data
            db.session.commit()

        flash(f'Sucessful set the weight!', 'success')
    
    return render_template("user/account_modules/weight_form.html", weight_form=weight_form)

@users.route("/account/update_influence_form", methods=['GET', 'POST'])
@login_required
def influence_form_submition():
    
    inf_form = inf_Form(prefix="influence")
    if inf_form.validate_on_submit():
        receiver = User.query.filter(func.lower(User.RSI_handle) == func.lower(inf_form.RSI_handle.data)).first()

        sent = current_user.send_tribute(receiver=receiver, amount=inf_form.amount.data, message = inf_form.message.data )
        if sent == 0:
            flash(f'Sucessful transfer of ' + str(inf_form.amount.data) + ' influence to ' + receiver.RSI_handle, 'success')
        else: 
            flash(f'error', 'danger')
    
    return render_template("user/account_modules/influence_form.html", inf_form=inf_form)
#================================================================================
''' @users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(RSI_handle=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('social/user_posts.html', posts=posts, user=user) '''


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instruction to reset your password', 'info')
        return redirect(url_for('users.login'))
    return render_template('user/reset_request.html', title="Reset Password", form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')

    form = ResetPasswordForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been updated! You can now login.', 'success')
        return redirect(url_for('users.login'))

    return render_template('user/reset_token.html', title="Reset Password", form=form)


@users.route("/confirm_email/<token>", methods=['GET', 'POST'])
def confirm_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('users.login'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
    else:
        user.email_confirmed = True
        db.session.commit()
        flash('Email confirm, please login!', 'success')

    return redirect(url_for('users.login'))


@scheduler.task("interval", id="password attempt", minutes = 30)
def reset_login_timer():
    users = User.query.filter(User.login_attempt >= 1).all()
    for user in users:
        user.login_attempt = 0
    print("Reset login attempt timer!")