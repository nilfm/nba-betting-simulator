from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

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
    away_team = db.Column(db.String(3), db.ForeignKey('team.short_name'))
    date = db.Column(db.String(20), index=True, default=datetime.utcnow().strftime('%Y-%m-%d'))
    
    db.UniqueConstraint(home_team, away_team, date)
    
    def __repr__(self):
        return f"<{self.away_team} @ {self.home_team}>"
            

class FinishedGame(Game):
    id = db.Column(db.Integer, db.ForeignKey('game.id'), primary_key=True)
    winner = db.Column(db.Integer) # 1 - home, 2 - away
    home_score = db.Column(db.Integer) 
    away_score = db.Column(db.Integer)
    
    def __repr__(self):
        return f"<Result: {self.away_score} - {self.home_score}>"

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'), index=True)
    amount = db.Column(db.Integer)
    bet_on_home = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
        
    def __repr__(self):
        bet_for = "for the home team" if self.bet_on_home else "for the away team"
        return f"<{user_id} bet {self.amount} on {self.game_id} {bet_for}>"

class FinishedBet(Bet):
    id = db.Column(db.Integer, db.ForeignKey('bet.id'), primary_key=True)
    won = db.Column(db.Boolean)
    balance = db.Column(db.Integer) # profits - amount bet (can be negative)
    
    def __repr__(self):
        return f"<Finished bet - balance: {self.balance}>"
