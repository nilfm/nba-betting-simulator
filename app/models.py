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
    date_reg = db.Column(db.DateTime, default=datetime.utcnow)
    
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
        self.funds += amount
        self.save_db()
    
    def reset_funds(self, amount=1000):
        self.funds = amount
        self.save_db()
    
    def save_db(self):
        db.session.add(self)
        db.session.commit()
        
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

class Team(db.Model):
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
    
    db.UniqueConstraint(home_team, away_team, date)
    
    def __repr__(self):
        return f"<{self.away_team} @ {self.home_team} on {self.date}>"
            

class FinishedGame(Game):
    id = db.Column(db.Integer, db.ForeignKey('game.id'), primary_key=True)
    game = db.relationship('Game', foreign_keys=[id])
    winner = db.Column(db.Integer) # 1 - home, 2 - away
    home_score = db.Column(db.Integer) 
    away_score = db.Column(db.Integer)
    
    def __repr__(self):
        return f"<Result: {self.away_score} - {self.home_score}>"

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    user = db.relationship('User', foreign_keys=[user_id])
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    game = db.relationship('Game', foreign_keys=[game_id])
    amount = db.Column(db.Integer)
    bet_on_home = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    db.UniqueConstraint(user_id, game_id, bet_on_home)

    def __repr__(self):
        bet_for = "for the home team" if self.bet_on_home else "for the away team"
        return f"<{self.user.username} bet {self.amount} on {self.game} {bet_for}>"

class FinishedBet(Bet):
    id = db.Column(db.Integer, db.ForeignKey('bet.id'), primary_key=True)
    bet = db.relationship('Bet', foreign_keys=[id])
    won = db.Column(db.Boolean)
    balance = db.Column(db.Integer) # profits - amount bet (can be negative)
    
    def __repr__(self):
        return f"<Finished bet - balance: {self.balance}>"
