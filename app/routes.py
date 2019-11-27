#!/usr/bin/env python3

import json
from datetime import datetime
from app import app, db
from app.forms import LoginForm, RegistrationForm, BetForm
from app.models import User
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

TODAY = datetime.now().strftime('%Y-%m-%d')
IN_FILE_PATH = f"../data/data_{TODAY}.txt"

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    with open(IN_FILE_PATH, 'r') as infile:
        games = json.load(infile)
    form = BetForm()
    if form.validate_on_submit():
        flash(form.amount.data)
        return redirect(url_for('index'))
    return render_template('index.html', games=games, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, funds=1000)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Successfully registered user {user.username}')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
    
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    bets = [
        {'home_team' : 'TOR', 'away_team' : 'DAL', 'amount' : 100, 'bet_on_home' : True},
        {'home_team' : 'POR', 'away_team' : 'GSW', 'amount' : 50, 'bet_on_home' : False}
    ]
    return render_template("user.html", user=user, bets=bets)
