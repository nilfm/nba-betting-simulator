#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from pprint import pprint
from app import app, db
from app.forms import *
from app.models import *
from app.email import *
from flask import render_template, jsonify, flash, redirect, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import subprocess


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    return render_template('index.html')

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

'''
Returns a list of days which each has a list of games which each has a list of bets on that game
'''
@app.route('/api/feed', methods=['GET'])
@login_required
def api_feed():
    bets = Bet.query.order_by(Bet.date_time.desc()).all()
    followed_bets = [b for b in bets if current_user.is_following(b.user)]
    days = sorted(set(b.game.date for b in followed_bets), reverse=True)
    bets_days = [
        {
        'day': day, 
        'games': 
            {
                b.game_id:
                {'info': b.game.to_dict(),
                'bets': 
                    [
                        e.to_dict() 
                        for e in followed_bets 
                        if e.game.date == day and e.game_id == b.game_id
                    ]
                } 
                for b in followed_bets if b.game.date == day
             }
        } 
        for day in days
    ]
    print(bets_days)
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

@app.route('/api/games', methods=['GET'])
@login_required
def api_games_today():
    TODAY = (datetime.utcnow()-timedelta(hours=8)).strftime('%Y-%m-%d')
    games = Game.query.filter_by(date=TODAY).all()
    already_bet_home = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=True).first() is not None for g in games]
    already_bet_away = [Bet.query.filter_by(game_id=g.id, user_id=current_user.id, bet_on_home=False).first() is not None for g in games]
    games = [g.to_dict() for g in games]
    for game, home, away in zip(games, already_bet_home, already_bet_away):
        game['already_bet_home'] = home
        game['already_bet_away'] = away
    return jsonify(games)


'''
Expected data:
{
    'game_id': INTEGER,
    'bet_on_home': BOOLEAN,
    'amount': INTEGER
}
where:
    -game_id is a valid game id for a game that hasn't started
    -amount is between 1 and current funds 
    -the user has not yet bet on this team for this game
    
Returns:
{
    'success': BOOLEAN,
    'msg': STRING
}    
where:
    -success is true if the bet has been placed successfully
    -msg is one of:
        -"You have successfully bet X coins on Y [team]"
        -"This game already started"
        -"This game doesn't exist"
        -"The bet amount has to be positive"
        -"You only have X coins"
        -"You have already bet on this game"
'''
@app.route('/api/place_bet', methods=['POST'])
@login_required
def api_place_bet():
    data = json.loads(request.get_data())
    response = current_user.place_bet(
        data['game_id'],
        data['amount'],
        data['bet_on_home']
    )
    return jsonify(response)

'''
Expected data: None

Returns:
{
    'success': BOOLEAN,
    'msg': STRING
}    
where:
    -success is true if the user has been followed successfully
    -msg is one of:
        -"You are now following X
        -"User not found"
        -"You cannot follow yourself"
        -"You were already following X"
'''
@app.route('/api/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    response = current_user.follow(user)
    return jsonify(response)

'''
Expected data: None

Returns:
{
    'success': BOOLEAN,
    'msg': STRING
}    
where:
    -success is true if the user has been unfollowed successfully
    -msg is one of:
        -"You are no longer following X
        -"User not found"
        -"You cannot unfollow yourself"
        -"You were already not following X"
'''
@app.route('/api/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    response = current_user.unfollow(user)
    return jsonify(response)
    

