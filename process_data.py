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
OUT_FILE_PATH = f"data_{TODAY}.txt"
IN_DIR = "raw"
OUT_DIR = "data"

def shorten_team(name):
    shortened = {
        'Atlanta Hawks' : 'ATL',
        'Boston Celtics' : 'BOS',
        'Brooklyn Nets' : 'BKN',
        'Charlotte Hornets' : 'CHA',
        'Chicago Bulls' : 'CHI',
        'Cleveland Cavaliers' : 'CLE',
        'Dallas Mavericks' : 'DAL',
        'Denver Nuggets' : 'DEN',
        'Detroit Pistons' : 'DET',
        'Golden State Warriors' : 'GSW',
        'Houston Rockets' : 'HOU',
        'Indiana Pacers' : 'IND',
        'Los Angeles Clippers' : 'LAC',
        'Los Angeles Lakers' : 'LAL',
        'Memphis Grizzlies' : 'MEM',
        'Miami Heat' : 'MIA',
        'Milwaukee Bucks' : 'MIL',
        'Minnesota Timberwolves' : 'MIN',
        'New Orleans Pelicans' : 'NOP',
        'New York Knicks' : 'NYK',
        'Oklahoma City Thunder' : 'OKC',
        'Orlando Magic' : 'ORL',
        'Philadelphia 76ers' : 'PHI',
        'Phoenix Suns' : 'PHO',
        'Portland Trail Blazers' : 'POR',
        'Sacramento Kings' : 'SAC',
        'San Antonio Spurs' : 'SAS',
        'Toronto Raptors' : 'TOR',
        'Utah Jazz' : 'UTA',
        'Washington Wizards': 'WAS'
    }
    return shortened[name]

def process_time(time):
    return datetime.fromtimestamp(time).strftime('%Y-%m-%d')

def process(game):
    site = sorted(game["sites"], key=lambda site: site['site_key'])[0]
    good_game = {
        'date_time' : process_time(site['last_update']),
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
    print(all_games)
    for game in data:
        g = Game(home_team=shorten_team(game['home_team']),
                 away_team=shorten_team(game['away_team']))
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
