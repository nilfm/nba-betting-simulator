from app import db
from app.models import *

games = Game.query.all()
bets = Bet.query.all()
users = User.query.all()
