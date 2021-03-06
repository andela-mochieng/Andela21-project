  
from flask import request, render_template, flash, g, session, redirect, url_for
from werkzeug import check_password_hash, generate_password_hash
from flask.ext.login import login_user, logout_user, current_user, login_required
from .. import db, login_manager
from . import auth
from app.model import User, Role, Post
from app.utils import send_email
from .forms import (LoginForm, Signup, ChangePassword, 
                    PasswordResetRequest,PasswordReset, ChangeEmail)

from flask_oauthlib.client import OAuth, OAuthException
from .. import oauth
facebook = oauth.remote_app(
    'facebook',
    consumer_key='654521371352208',
    consumer_secret='0e9043c8140ca7d6e474c8b6f3e55952',
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    ''' user details are queried if found redirected
     to main else remain on the same page login
    '''
    if  current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm() 
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        flash('Sign up to gain access')

        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            return redirect(next or url_for('main.index')) # needs correction.
            flash('Welcome %s' % user.name)
        flash('Incorrect password or email')    
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    ''' logout user'''
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    form = Signup()
    if form.validate_on_submit():
        user = User(name =form.name.data,
                    email=form.email.data,
                    password= form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(
                    user.email, 'Confirmed Your store Account', 'auth/email/confirm',
                    user=user, token=token)
        flash('Check your email for the confirmation Email from us!')
        login_user(user,form.password.data)
        return redirect(url_for('main.index'))
    return render_template('auth/signup.html', form=form)
    
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('Welcome, {}! Thank you for verifying your Account!'.format(current_user.name))
        return redirect(url_for('main.index'))
    else:
        flash('The confirmation link has expired or is Invalid')
    return redirect(url_for('main.index'))
    

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Email','auth/email/confirm',
                user=current_user, token=token)
    flash('We have sent a new confirmation email')
    return redirect(url_for('main.index'))


# continue verification


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePassword()
    if form.validate_on_submit():
        if current_user.verify_passsword(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('Password has been updated')
            return redirect(url_for('main.index'))
        else:
            flash('Password is Invalid')
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset', methods=['GET','POST'])
def password_reset_request():
    ''' users who request for a password change '''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequest()     

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_confirmation_token()
            send_email(
                        user.email, 'Reset your password', 'auth/email/reset_password',
                        user=user, token=token, next=request.args.get('next'))
            flash('we have send an email with instruction how to reset your password')
            return redirect(url_for('auth.login'))
        else:
            flash('No account found with that email address')
            return redirect(url_for('auth.change_password', form=form)) 
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET','POST'])
def password_reset(token):
    '''users get tokens sent to their password to change their password '''
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordReset()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash('No account found with that email address')
            return redirect(url_for('main.index'))

        if user.resetPassword(token, form.password.data):
            flash('Your Password has been updated')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/password_reset.html', form= form)

@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    ''' user request to change their passwords '''
    form = ChangeEmail()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            
            send_email(
                        new_email,'Confirm your email Address', 'auth/email/change_email',
                        user= current_user, token=token)
            flash('We have send an email with instruction how to reset your password')
            return redirected(url_for('main.index'))
        else:
            flash('Password is Invalid')
    return render_template('auth/change_email.html', form=form)
                

@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    ''' tokens set to reset their emails'''
    if current_user.change_email(token):
        flash('Your email address hass been updated')
    else:
        flash('Invalid request')
    return redirect(url_for('main.index'))        

# facebook login
@auth.route('/fb_login')
def fb_login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)


@auth.route('/login/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message

    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    print 'Logged in as id=%s name=%s redirect=%s' % \
        (me.data['id'], me.data['name'], request.args.get('next'))
    return redirect(url_for('main.index'))

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')