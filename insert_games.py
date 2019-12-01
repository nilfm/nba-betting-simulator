#!/usr/bin/env python3

import json
import requests
from datetime import datetime
import os
from app import db
from app.models import Game, Bet
from sqlalchemy.exc import IntegrityError
import settings

ODDS_API_KEY = os.getenv('ODDS_API_KEY')
ODDS_URL = f"https://api.the-odds-api.com/v3/odds/?apiKey={ODDS_API_KEY}&sport=basketball_nba&region=us&mkt=h2h"
TODAY = datetime.now().strftime('%Y-%m-%d')
RAW_DIR = "raw"
DATA_DIR = "odds"
RAW_FILE_PATH = f"raw_{TODAY}.txt"
DATA_FILE_PATH = f"data_{TODAY}.txt"
TEAMS_FILE_PATH = "teams.json"
TIME_DIFFERENCE = 3600*8    # Avoids situation with games at 11 pm and 1 am on "different days"

def get():
    r = requests.get(ODDS_URL)
    return r.json()
    
def write_to_raw_file():
    data = get()
    with open(os.path.join(RAW_DIR, RAW_FILE_PATH), 'w') as outfile:
        json.dump(data, outfile, indent=4)

def shorten_team(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['team_name'] : t['short_name'] for t in teams}
    return shortened[name]

def format_datetime(time):
    return datetime.fromtimestamp(time-TIME_DIFFERENCE).strftime('%Y-%m-%d %H:%M:%S')
    
def format_date(time):
    return datetime.fromtimestamp(time-TIME_DIFFERENCE).strftime('%Y-%m-%d')

def process(game):
    site = sorted(game["sites"], key=lambda site: site['site_key'])[0]
    good_game = {
        'date_time' : format_datetime(game['commence_time']),
        'date' : format_date(game['commence_time']),
        'site' : site["site_key"],
        'home_team' : game["home_team"],
        'away_team' : game["teams"][0] if game["home_team"] != game["teams"][0] else game["teams"][1],
        'home_odds' : site['odds']['h2h'][1] if game["home_team"] == game["teams"][1] else site['odds']['h2h'][0],
        'away_odds' : site['odds']['h2h'][1] if game["home_team"] == game["teams"][0] else site['odds']['h2h'][0],
    }    
    return good_game

def process_data(data):
    good_data = [process(game) for game in data["data"] if game['sites_count'] > 0]
    return good_data

def read_raw_data():
    with open(os.path.join(RAW_DIR, RAW_FILE_PATH), 'r') as infile:
        data = json.load(infile)
    return data

def write_to_data_file(data):
    with open(os.path.join(DATA_DIR, DATA_FILE_PATH), 'w') as outfile:
        json.dump(data, outfile, indent=4)

def write_to_db(data):
    all_games = Game.query.all()
    for game in data:
        g = Game(home_team=shorten_team(game['home_team']),
                 away_team=shorten_team(game['away_team']),
                 home_odds=game['home_odds'],
                 away_odds=game['away_odds'],
                 date=game['date'],
                 date_time=game['date_time'])
        try:
            db.session.add(g)
            db.session.commit()
            print(g)
        except IntegrityError:
            db.session.rollback()
            game = Game.query.filter_by(home_team=g.home_team, away_team=g.away_team, date=g.date).first()
            game.update_odds(g.home_odds, g.away_odds)
            db.session.commit()
            print('Updated ', game)

def process_and_save():
    data = read_raw_data()
    processed = process_data(data)
    write_to_data_file(processed)
    write_to_db(processed)

def main():
    write_to_raw_file()
    process_and_save()

if __name__ == '__main__':
    main()
