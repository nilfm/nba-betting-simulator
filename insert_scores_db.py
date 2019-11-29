import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app import db
from app.models import *
from sqlalchemy.exc import IntegrityError

YESTERDAY_URL = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
SCORES_DIR = 'scores'
SCORES_FILE_PATH = f'scores_{YESTERDAY}.txt'
TEAMS_FILE_PATH = 'teams.json'

def shorten_team(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['simple_name'] : t['short_name'] for t in teams}
    return shortened[name]

def finish_game(game, score):
    try:
        game.finish(score['home_score'], score['away_score'])
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        
def finish_bets(game, score):
    bets = Bet.query.filter_by(game_id = game.id).all()
    for bet in bets:
        home_won = score['home_score'] > score['away_score']
        right = bet.bet_on_home == home_won
        try:
            bet.finish(right)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            
            
def write_to_db(scores):
    for score in scores:
        games = Game.query.filter_by(date=YESTERDAY, home_team=score['home_team'], away_team=score['away_team']).all()
        if len(games) == 1:
            game = games[0]
            finish_game(game, score)
            finish_bets(game, score)

def main():
    with open(os.path.join(SCORES_DIR, SCORES_FILE_PATH), 'r') as infile:
        scores = json.load(infile)
    print(scores)
    write_to_db(scores)

if __name__ == '__main__':
    main()
