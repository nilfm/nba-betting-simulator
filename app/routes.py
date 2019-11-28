#!/usr/bin/env python3

import json
from datetime import datetime
from app import app, db
from app.forms import LoginForm, RegistrationForm, BetForm
from app.models import User, Game, Bet
from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY = '2019-11-29'
IN_FILE_PATH = f"../data/data_{TODAY}.txt"

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    games = Game.query.filter_by(date=TODAY).all()
    forms = [BetForm(prefix=str(i)) for i in range(len(games)*2)]
    games_forms = list(zip(games, forms[::2], forms[1::2]))
    for game, form1, form2 in games_forms:
        for i, form in enumerate([form1, form2]):
            if form.submit.data and form.validate_on_submit():
                bet_on_home = (i == 0)
                correct_bet = current_user.place_bet(game, form.amount.data, bet_on_home)
                if (correct_bet):
                    flash(f"You have successfully bet {form.amount.data} coin(s) on {game.home_team if bet_on_home else game.away_team}. You now have {current_user.funds} coin(s).")
                else:
                    flash("You already bet on this team for this game.")
                return redirect(url_for('index'))

    return render_template('index.html', games_forms=games_forms, date=TODAY)

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
    bets = Bet.query.filter_by(user_id=user.id).all()
    return render_template("user.html", title=f"{username}'s profile",user=user, bets=bets)

@app.route('/proves', methods=['GET', 'POST'])
@login_required
def proves():
    forms = [BetForm(prefix=str(i)) for i in range(3)]
    for form in forms:
        if form.validate_on_submit():
            flash(f"You have successfully bet {form.amount.data}")
            return redirect(url_for('proves'))
    return render_template('prova.html', forms=forms)

@app.route('/ranking')
def ranking():
    users = User.query.order_by(User.funds.desc())
    ranks = [(i, u.username, u.funds) for i, u in enumerate(users, start=1)]
    return render_template('ranking.html', title='Ranking', ranking=ranks)
