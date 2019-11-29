import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app import db
from app.models import *
from sqlalchemy.exc import IntegrityError

YESTERDAY_URL = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
YESTERDAY = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') # maybe I actually need YESTERDAY
URL = f'https://www.cbssports.com/nba/scoreboard/{YESTERDAY_URL}/'
SCORES_DIR = 'scores'
SCORES_FILE_PATH = f'scores_{YESTERDAY}.txt'
TEAMS_FILE_PATH = 'teams.json'

def shorten_team(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['simple_name'] : t['short_name'] for t in teams}
    return shortened[name]

def get_scores():
    games = []

    page = requests.get(URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    tables=soup.findAll("div", {"class": "in-progress-table section"})

    for table in tables:
        game = {'scores': [], 'teams': []}
        rows = table.findAll('tr')
        for tr in rows:
            cols = tr.findAll('td')
            if cols:
                game['scores'].append(cols[-1].find(text=True))
            names = tr.findAll('a')
            for name in names:
                if name.string != None:
                    game['teams'].append(name.string)
        if (game):
            games.append(game)

    good_games = [
        {
            'away_team' : shorten_team(game['teams'][0]),
            'away_score' : game['scores'][0],
            'home_team' : shorten_team(game['teams'][1]),
            'home_score' : game['scores'][1]
        }
        for game in games
    ]
    return good_games

def write_scores_to_file(scores):
    with open(os.path.join(SCORES_DIR, SCORES_FILE_PATH), 'w') as outfile:
        json.dump(scores, outfile, indent=4)

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
        games = Game.query.filter_by(date=TODAY, away_team=score['home_team'], home_team=score['away_team']).all()
        if len(games) == 1:
            game = games[0]
            finish_game(game, score)
            finish_bets(game, score)


if __name__ == '__main__':
    scores = get_scores()
    write_scores_to_file(scores)
    write_to_db(scores)
