#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from app import app, db
from app.forms import LoginForm, RegistrationForm, BetForm
from app.models import User, Game, Bet
from flask import render_template, jsonify, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

TODAY = (datetime.now()-timedelta(hours=8)).strftime('%Y-%m-%d')
IN_FILE_PATH = f"../odds/data_{TODAY}.txt"

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    games = Game.query.filter_by(date=TODAY).all()
    already_bet_home = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=True).first() is not None for g in games]
    already_bet_away = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=False).first() is not None for g in games]
    # Filter out games that have already started, need to filter out already_bet_X too
    not_started = [(game, b1, b2)for game, b1, b2 in zip(games, already_bet_home, already_bet_away) if datetime.strptime(game.date_time, '%Y-%m-%d %H:%M:%S') > datetime.now() - timedelta(hours=8)]
    # zip(*x) is the inverse of zip
    games, already_bet_home, already_bet_away = zip(*not_started)
    
    forms = [BetForm(prefix=str(i)) for i in range(len(games)*2)]
    games_forms = list(zip(games, forms[::2], forms[1::2], already_bet_home, already_bet_away))
    for game, form1, form2, _, _ in games_forms:
        for i, form in enumerate([form1, form2]):
            if form.submit.data and form.validate_on_submit():
                bet_on_home = (i == 0)
                correct_bet = current_user.place_bet(game, form.amount.data, bet_on_home)
                if (correct_bet):
                    flash(f"You have successfully bet {form.amount.data} coin{'s' if form.amount.data != 1 else ''} on {game.home_team if bet_on_home else game.away_team}. You now have {current_user.funds} coin{'s' if current_user.funds != 1 else ''}.")
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
    bets = sorted(bets, key=lambda b: datetime.strptime(b.game.date, '%Y-%m-%d'), reverse=True)
    pending_bets = [bet for bet in bets if not bet.finished]
    finished_bets = [bet for bet in bets if bet.finished]
    num_won = sum(bet.won for bet in finished_bets)
    stats = {
        'won': num_won,
        'lost': len(finished_bets) - num_won,
        'pending': len(pending_bets) 
    }
    is_me = user.id == current_user.id
    return render_template("user.html", title=f"{username}'s profile", stats=stats, is_me=is_me, user=user, pending_bets=pending_bets, finished_bets=finished_bets)

@app.route('/proves', methods=['GET', 'POST'])
@login_required
def proves():
    games = Game.query.filter_by(date=TODAY).all()
    forms = [BetForm(prefix=str(i)) for i in range(len(games)*2)]
    games_forms = list(zip(games, forms[::2], forms[1::2]))
    return render_template('prova.html', games_forms=games_forms, date=TODAY)

@app.route('/ranking')
def ranking():
    users = User.query.order_by(User.ranking_funds.desc())
    ranks = [(i, u.username, u.ranking_funds) for i, u in enumerate(users, start=1)]
    return render_template('ranking.html', title='Ranking', ranking=ranks)

@app.route('/reset_account', methods=['POST'])
@login_required
def reset_account():
    current_user.reset_account()
    flash('Your account has been reset')
    return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    id = current_user.id
    logout_user()
    User.query.filter_by(id=id).delete()
    Bet.query.filter_by(user_id=id).delete()
    db.session.commit()
    return redirect(url_for('login'))
