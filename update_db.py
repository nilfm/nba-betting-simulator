from app import db
from app.models import *

# Update user's ranking funds
users = User.query.all()
for user in users:
    amt = user.funds
    bets = Bet.query.filter_by(user_id = user.id, finished=False).all()
    for bet in bets:
        amt += bet.amount
    user.ranking_funds = amt
    db.session.commit()
    
# Update bet's odds
bets = Bet.query.all()
for bet in bets:
    odds = bet.game.home_odds if bet.bet_on_home else bet.game.away_odds
    bet.odds = odds
    db.session.commit()
    
