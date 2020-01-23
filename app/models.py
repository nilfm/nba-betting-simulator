from app import app, db, login
from app.search import add_to_index, remove_from_index, query_index
from datetime import datetime, timedelta
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError
import jwt

class SearchableMixin():
    @classmethod
    def search(cls, expression, amount):
        ids, total = query_index(cls.__tablename__, expression, amount=amount)
        if total == 0:
            return cls.query.filter_by(id=0).all(), 0
        when = []
        for i, id in enumerate(ids):
            when.append((id, i))
        return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)).all(), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(SearchableMixin, UserMixin, db.Model):
    __searchable__ = ['username']
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    funds = db.Column(db.Integer)
    ranking_funds = db.Column(db.Integer, index=True)
    date_reg = db.Column(db.DateTime, default=datetime.utcnow)
    
    followed = db.relationship(
        'User', 
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
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

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_users(self):
        followed =  User.query.join(
            followers, (followers.c.followed_id == User.id)).filter(followers.c.follower_id == self.id)
        me = User.query.filter_by(id=self.id)
        return followed.union(me).order_by(User.ranking_funds.desc()).all()

    def place_bet(self, game_id, amount, bet_on_home):
        # Avoid bets on games that have already started
        game = Game.query.filter_by(id=game_id).first()
        if (game is None):
            return {
                'success': False,
                'msg': "This game doesn't exist"
            }
        if datetime.strptime(game.date_time, '%Y-%m-%d %H:%M:%S') < datetime.now() - timedelta(hours=8):
            return {
                'success': False,
                'msg': "This game already started"
            }
        if amount > self.funds:
            return {
                'success': False,
                'msg': f"You only have {self.funds} coins"
            }
        if amount <= 0:
            return {
                'success': False,
                'msg': "The bet amount has to be positive"
            }
        bet = Bet(
            user_id=self.id,
            game_id=game.id,
            amount=amount,
            odds=game.home_odds if bet_on_home else game.away_odds,
            bet_on_home=bet_on_home
        )
        try:
            db.session.add(bet)
            db.session.commit()
            self.change_balance(-amount)
            team_name = game.home_team if bet_on_home else game.away_team
            return {
                'success': True,
                'msg': f"You have successfully bet {amount} coins on {team_name}"
            }
        except IntegrityError as e:
            return {
                'success': False,
                'msg': "You have already bet on this game"
            }
                
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
        self.ranking_funds = int(amount)
        db.session.commit()
    
    def to_dict(self):
        user_dict = {
            'id': self.id,
            'username': self.username,
            'funds': self.funds,
            'ranking_funds': self.ranking_funds
        }
        return user_dict
    
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))
        
    def get_reset_password_token(self, expires_in=600):
        data = {
            'reset_password': self.id,
            'exp': time() + expires_in
        }
        return jwt.encode(data, app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)

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

    def update_odds(self, home_odds, away_odds):
        self.home_odds = home_odds
        self.away_odds = away_odds

    def finish(self, home_score, away_score):
        if self.finished:
            return
        self.finished = True
        self.home_score = home_score
        self.away_score = away_score
        self.winner = 1 if home_score > away_score else 2
        print(self)
    
    def to_dict(self):
        game_dict = {
            'game_id': self.id,
            'home_team': {
                'short': self.home_team_long.short_name,
                'long': self.home_team_long.long_name,
                'odds': self.home_odds,
                'score': self.away_score
            },
            'away_team': {
                'short': self.away_team_long.short_name,
                'long': self.away_team_long.long_name,
                'odds': self.away_odds,
                'score': self.away_score
            },
            'finished': self.finished,
            'winner': self.winner,
            'date_time': self.date_time,
            'date': self.date
        }
        return game_dict
    
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
    date_time = db.Column(db.String(40), index=True)
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
        self.date_time = (datetime.utcnow() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        
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
    
    def to_dict(self):
        bet_dict = {
            'user_id': self.user_id,
            'username': self.user.username,
            'game_id': self.game.id,
            'home_team': {
                'short': self.game.home_team_long.short_name,
                'long': self.game.home_team_long.long_name
            },
            'away_team': {
                'short': self.game.away_team_long.short_name,
                'long': self.game.away_team_long.long_name
            },
            'bet_for_team': {
                'short': self.game.home_team_long.short_name if self.bet_on_home else self.game.away_team_long.short_name,
                'long': self.game.home_team_long.long_name if self.bet_on_home else self.game.away_team_long.long_name,
            },
            'bet_on_home': self.bet_on_home,
            'finished': self.finished,
            'amount': self.amount,
            'odds': self.odds,
            'won': self.won,
            'balance': self.balance,
            'date_time': self.date_time,
            'game_date': self.game.date
        }
        return bet_dict
    
    def __repr__(self):
        bet_for = "for the home team" if self.bet_on_home else "for the away team"
        if self.won is None:
            return f"<{self.user.username} bet {self.amount} on {self.game} {bet_for}>"
        else:
            did_win = "won" if self.won else "lost"
            return f"<{self.user.username} bet {self.amount} on {self.game} {bet_for} and {did_win}>"

class TimestampGames(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True)
    api_remaining = db.Column(db.Integer)
    
    def __init__(self, api_remaining):
        self.timestamp = datetime.now() + timedelta(hours=1)
        self.api_remaining = api_remaining
    
    def __repr__(self):
        date_time = self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return f"{date_time} - {self.api_remaining} calls left"
    
class TimestampScores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True)
    
    def __init__(self):
        self.timestamp = datetime.now() + timedelta(hours=1)
    
    def __repr__(self):
        return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')


