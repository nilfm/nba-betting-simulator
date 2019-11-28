#!/usr/bin/env python3

import json
import pprint
from datetime import datetime
import os
from app import db
from app.models import Game
from sqlalchemy.exc import IntegrityError

TODAY = datetime.now().strftime('%Y-%m-%d')
IN_FILE_PATH = f"raw_{TODAY}.txt"
TEAMS_FILE_PATH = "teams.json"
OUT_FILE_PATH = f"data_{TODAY}.txt"
IN_DIR = "raw"
OUT_DIR = "data"

def shorten_team(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['team_name'] : t['short_name'] for t in teams}
    return shortened[name]

def process_time(time):
    return datetime.fromtimestamp(time-3600*8).strftime('%Y-%m-%d %H:%M:%S')
    
def process_date(time):
    return datetime.fromtimestamp(time-3600*8).strftime('%Y-%m-%d')

def process(game):
    site = sorted(game["sites"], key=lambda site: site['site_key'])[0]
    good_game = {
        'date_time' : process_time(game['commence_time']),
        'date' : process_date(game['commence_time']),
        'odds' : site["odds"]["h2h"][::-1], # odds[0] referred to teams[1] and viceversa if I didn't do this
        'site' : site["site_key"],
        'home_team' : game["teams"][1],
        'away_team' : game["teams"][0],
        'teams' : game["teams"]
    }
    
    return good_game

def process_data(data):
    good_data = [process(game) for game in data["data"] if game['sites_count'] > 0]
    return good_data

def read_data():
    with open(os.path.join(IN_DIR, IN_FILE_PATH), 'r') as infile:
        data = json.load(infile)
    return data

def write_to_file(data):
    with open(os.path.join(OUT_DIR, OUT_FILE_PATH), 'w') as outfile:
        json.dump(data, outfile, indent=4)

def write_to_db(data):
    all_games = Game.query.all()
    for game in data:
        g = Game(home_team=shorten_team(game['home_team']),
                 away_team=shorten_team(game['away_team']),
                 date=game['date'])
        try:
            db.session.add(g)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
    
def daily_save():
    data = read_data()
    processed = process_data(data)
    write_to_file(processed)
    write_to_db(processed)

def main():
    daily_save()

if __name__ == '__main__':
    main()
