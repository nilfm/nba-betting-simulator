#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from pprint import pprint
from app import app, db
from app.forms import *
from app.models import *
from app.email import *
from flask import get_flashed_messages, render_template, jsonify, flash, redirect, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import subprocess


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    TODAY = (datetime.now()-timedelta(hours=8)).strftime('%Y-%m-%d')
    games = Game.query.filter_by(date=TODAY).all()
    already_bet_home = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=True).first() is not None for g in games]
    already_bet_away = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=False).first() is not None for g in games]
    # Filter out games that have already started, need to filter out already_bet_X too
    not_started = [(game, b1, b2) for game, b1, b2 in zip(games, already_bet_home, already_bet_away) if datetime.strptime(game.date_time, '%Y-%m-%d %H:%M:%S') > datetime.now() - timedelta(hours=8)]
    # zip(*x) is the inverse of zip
    if not_started:
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
                    flash('There was an error processing your bet.')
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
        return redirect(url_for('index'))
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
    
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
    
@app.route('/user/<username>')
@login_required
def user(username):
    return render_template("user.html", title=f"{username}'s profile", username=username)

@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(f'You are now following {username}!')
    return redirect(url_for('user', username=username))

@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.')
        return redirect(url_for('index'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are no longer following {username}.')
    return redirect(url_for('user', username=username))

@app.route('/proves', methods=['GET', 'POST'])
@login_required
def proves():
    TODAY = (datetime.now()-timedelta(hours=8)).strftime('%Y-%m-%d')
    games = Game.query.filter_by(date=TODAY).all()
    forms = [BetForm(prefix=str(i)) for i in range(len(games)*2)]
    games_forms = list(zip(games, forms[::2], forms[1::2]))
    return render_template('prova.html', games_forms=games_forms, date=TODAY)

@app.route('/ranking')
def ranking():
    return render_template('ranking.html', title='Ranking')

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

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username != "nilfm":
        return redirect(url_for('index'))
    last_games = TimestampGames.query.order_by(TimestampGames.timestamp.desc()).first()
    last_scores = TimestampScores.query.order_by(TimestampScores.timestamp.desc()).first()
    return render_template('admin.html', last_games=last_games, last_scores=last_scores)
    
@app.route('/execute/<name>', methods=['POST'])
@login_required
def execute(name):
    if current_user.username != "nilfm":
        return redirect(url_for('index'))    
    subprocess.call(f'./{name}', shell=True)
    flash(f'Script {name} called')
    return redirect(url_for('admin'))

@app.before_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()

@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('index'))
    users, total = User.search(g.search_form.q.data.lower(), 5)
    return render_template('search.html', title='Search', users=users, total=len(users))

@app.route('/feed')
@login_required
def feed():
    return render_template('feed.html', title='Feed')

@app.route('/api/flashed_messages', methods=['GET'])
def flashed_messages():
    return jsonify([{'text': message} for message in get_flashed_messages()])

def custom_key(x):
    mapping = {
        'Me': 0,
        'Following': 1,
        'Not Following': 2 
    }
    return mapping[x['data']['category']], x['value']

@app.route('/api/users', methods=['GET'])
def api_users():
    if not current_user.is_authenticated:
        return jsonify(None)
    users = User.query.all()
    params = [
        {
            'value': u.username,
            'data': { 'category': 'Following' if current_user.is_following(u) else 'Me' if current_user.id == u.id else 'Not Following' }
        }
        for u in users
    ]
    params = sorted(params, key=custom_key)
    return jsonify(params)

@login_required
@app.route('/api/user/<username>', methods=['GET'])
def api_user(username):
    user = User.query.filter_by(username=username).first_or_404()
    bets = Bet.query.filter_by(user_id=user.id).all()
    pending_bets = [bet for bet in bets if not bet.finished]
    finished_bets = [bet for bet in bets if bet.finished]
    days = sorted(set(bet.game.date for bet in finished_bets), reverse=True)
    num_won = sum(bet.won for bet in finished_bets)
    stats = {
        'won': num_won,
        'lost': len(finished_bets) - num_won,
        'pending': len(pending_bets) 
    }
    data = {
        'is_following': current_user.is_following(user),
        'is_current': current_user.id == user.id,
        'stats': stats,
        'pending_bets': [bet.to_dict() for bet in pending_bets],
        'finished_bets': [{'day': day, 'bets': [bet.to_dict() for bet in finished_bets if bet.game.date == day]} for day in days],
    }
    data.update(user.to_dict())
    return jsonify(data)
        
@app.route('/api/current_user', methods=['GET'])
def api_current_user():
    data = {
        'is_authenticated': current_user.is_authenticated,
        'data': None if not current_user.is_authenticated else current_user.to_dict()
    }
    return jsonify(data)

@app.route('/api/feed', methods=['GET'])
@login_required
def api_feed():
    bets = Bet.query.order_by(Bet.date_time.desc()).all()
    followed_bets = [b for b in bets if current_user.is_following(b.user)]
    days = sorted(set(b.game.date for b in followed_bets), reverse=True)
    bets_days = [
        {'day': day, 'bets': [b.to_dict() for b in followed_bets if b.game.date == day]} for day in days
    ]
    return jsonify(bets_days);


@app.route('/api/ranking', methods=['GET'])
def api_ranking():
    users = User.query.order_by(User.ranking_funds.desc()).all()
    users = [u.to_dict() for u in users]
    
    followed = None
    if current_user.is_authenticated:
        followed = current_user.followed_users()
        followed = [u.to_dict() for u in followed]
    
    ranking = {
        'global': users,
        'followed': followed,
    }

    return jsonify(ranking)
