from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    funds = db.Column(db.Integer)
    ranking_funds = db.Column(db.Integer)
    date_reg = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, username, email, funds=1000):
        self.username = username
        self.email = email
        self.funds = funds
        self.ranking_funds = funds
    
    def __repr__(self):
        return f"<User {self.username} - {self.funds} coins>"
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def place_bet(self, game, amount, bet_on_home):
        bet = Bet(
            user_id=self.id,
            game_id=game.id,
            amount=amount,
            odds=self.home_odds if bet_on_home else self.away_odds,
            bet_on_home=bet_on_home
        )
        try:
            db.session.add(bet)
            db.session.commit()
            self.change_balance(-amount)
            return True
        except IntegrityError as e:
            db.session.rollback()
            return False
                
    def change_balance(self, amount):
        if (self.funds + amount < 0):
            raise ValueError('Insufficient funds!')
        self.funds += int(amount)
        db.session.commit()
    
    def change_ranking_balance(self, amount):
        self.ranking_funds += int(amount)
        db.session.commit()
    
    def reset_account(self):
        self.reset_funds()
        Bet.query.filter_by(user_id = self.id).delete()
        db.session.commit()
    
    def reset_funds(self, amount=1000):
        self.funds = int(amount)
        db.session.commit()
    
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

class Team(db.Model):
    def __init__(self, short_name, long_name):
        self.short_name = short_name
        self.long_name = long_name
    
    short_name = db.Column(db.String(3), primary_key=True)
    long_name = db.Column(db.String(50), unique=True)
    
    def __repr__(self):
        return f"<{self.short_name} - {self.long_name}>"

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(3), db.ForeignKey('team.short_name'))
    home_team_long = db.relationship('Team', foreign_keys=[home_team])
    away_team = db.Column(db.String(3), db.ForeignKey('team.short_name'))
    away_team_long = db.relationship('Team', foreign_keys=[away_team])
    home_odds = db.Column(db.Float())
    away_odds = db.Column(db.Float())
    date = db.Column(db.String(20), index=True, default=datetime.utcnow().strftime('%Y-%m-%d'))
    date_time = db.Column(db.String(40), index=True, default=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))    
    winner = db.Column(db.Integer) # None - unfinished, 1 - home, 2 - away
    home_score = db.Column(db.Integer) # None - unfinished
    away_score = db.Column(db.Integer) # None - unfinished
    finished = db.Column(db.Boolean)

    db.UniqueConstraint(home_team, away_team, date)
    
    def __init__(self, home_team, away_team, home_odds, away_odds, date, date_time):
        self.home_team = home_team
        self.away_team = away_team
        self.home_odds = home_odds
        self.away_odds = away_odds
        self.date = date
        self.date_time = date_time        
        self.finished = False

    def finish(self, home_score, away_score):
        if self.finished:
            return
        self.finished = True
        self.home_score = home_score
        self.away_score = away_score
        self.winner = 1 if home_score > away_score else 2
        print(self)
    
    def __repr__(self):
        if self.winner is None:
            return f"<{self.away_team} @ {self.home_team} on {self.date}>"
        else:
            return f"<{self.away_team} ({self.away_score}) @ {self.home_team} ({self.home_score}) on {self.date}>"

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    user = db.relationship('User', foreign_keys=[user_id])
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    game = db.relationship('Game', foreign_keys=[game_id])
    amount = db.Column(db.Integer)
    odds = db.Column(db.Float)
    bet_on_home = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, index=True)
    won = db.Column(db.Boolean)
    balance = db.Column(db.Integer) # profits - amount bet (can be negative)
    finished = db.Column(db.Boolean)

    db.UniqueConstraint(user_id, game_id, bet_on_home)
    
    def __init__(self, user_id, game_id, amount, odds, bet_on_home):
        self.user_id = user_id
        self.game_id = game_id
        self.amount = amount
        self.odds = odds
        self.bet_on_home = bet_on_home
        self.finished = False
        
    def update_odds(self, odds):
        self.odds = odds

    def finish(self, won):
        if self.finished:
            return
        self.finished = True
        self.won = won
        if won:
            self.balance = int(self.amount*(self.odds-1))
            self.user.change_balance(self.balance + self.amount)
            self.user.change_ranking_balance(self.balance)
        else:
            self.balance = -self.amount
            self.user.change_ranking_balance(-self.amount)
        print(self)
    
    def __repr__(self):
        bet_for = "for the home team" if self.bet_on_home else "for the away team"
        if self.won is None:
            return f"<{self.user.username} bet {self.amount} on {self.game} {bet_for}>"
        else:
            did_win = "won" if self.won else "lost"
            return f"<{self.user.username} bet {self.amount} on {self.game} {bet_for} and {did_win}>"
