#!/usr/bin/env python3

import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from app import db
from app.models import *
from sqlalchemy.exc import IntegrityError

YESTERDAY = {}
YESTERDAY['datetime_url'] = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
YESTERDAY['datetime_file'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
YESTERDAY['url'] = f'https://www.cbssports.com/nba/scoreboard/{YESTERDAY["datetime_url"]}/'
YESTERDAY['scores_file_path'] = f'scores_{YESTERDAY["datetime_file"]}.txt'

TODAY = {}
TODAY['datetime_url'] = datetime.now().strftime('%Y%m%d')
TODAY['datetime_file'] = datetime.now().strftime('%Y-%m-%d')
TODAY['url'] = f'https://www.cbssports.com/nba/scoreboard/{TODAY["datetime_url"]}/'
TODAY['scores_file_path'] = f'scores_{TODAY["datetime_file"]}.txt'

RECORDS_URL = 'https://www.cbssports.com/nba/standings/'

SCORES_DIR = 'scores'
TEAMS_FILE_PATH = 'teams.json'

def shorten_team(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['simple_name'] : t['short_name'] for t in teams}
    return shortened[name]

def shorten_team_records(name):
    with open(TEAMS_FILE_PATH, 'r') as infile:
        teams = json.load(infile)
        
    shortened = {t['records_name'] : t['short_name'] for t in teams}
    return shortened[name]

def get_scores(day):
    games = []

    page = requests.get(day['url'])
    soup = BeautifulSoup(page.text, 'html.parser')
    all_games = soup.findAll("div", {"class": "live-update"})
    for g in all_games:
        # Find finished games
        finished = g.findAll("div", {"class": "postgame"})
        if finished:
            # Get table of results
            table = g.findAll("div", {"class": "in-progress-table section"})[0]
            # Init dictionary
            game = {'scores': [], 'teams': []}
            rows = table.findAll('tr')
            for tr in rows:
                names = tr.findAll('a')
                for name in names:
                    if name.string != None:
                        game['teams'].append(name.string)
                cols = tr.findAll('td')
                if cols:
                    game['scores'].append(cols[-1].find(text=True))

            games.append(game)
                
    good_games = [
        {
            'away_team' : shorten_team(game['teams'][0]),
            'away_score' : game['scores'][0],
            'home_team' : shorten_team(game['teams'][1]),
            'home_score' : game['scores'][1]
        }
        for game in games if len(game['scores']) == 2
    ]
    return good_games

def write_scores_to_file(day, scores):
    with open(os.path.join(SCORES_DIR, day['scores_file_path']), 'w') as outfile:
        json.dump(scores, outfile, indent=4)

def finish_game(game, score):
    try:
        game.finish(int(score['home_score']), int(score['away_score']))
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        
def finish_bets(game, score):
    bets = Bet.query.filter_by(game_id = game.id).all()
    for bet in bets:
        home_won = int(score['home_score']) > int(score['away_score'])
        right = bet.bet_on_home == home_won
        try:
            bet.finish(right)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            
            
def write_to_db(day, scores):
    for score in scores:
        games = Game.query.filter_by(date=day['datetime_file'], home_team=score['home_team'], away_team=score['away_team']).all()
        if len(games) == 1:
            game = games[0]
            finish_game(game, score)
            finish_bets(game, score)

def save_timestamp():
    t = TimestampScores()
    db.session.add(t)
    db.session.commit()

def get_records():
    records = {}
    page = requests.get(RECORDS_URL)
    soup = BeautifulSoup(page.text, 'html.parser')
    table = soup.findAll("tr", {"class": "TableBase-bodyTr"})
    for tr in table:
        name = tr.findAll("span", {"class": "TeamName"})[0].string
        tds = tr.findAll("td", {"class": "TableBase-bodyTd--number"})
        short_name = shorten_team_records(name)
        records[short_name] = {
            'wins': int(tds[0].string.strip()),
            'losses': int(tds[1].string.strip()),
        }
    return records

def write_records_to_db(records):
    for team, record in records.items():
        t = Team.query.filter_by(short_name = team).first()
        t.wins = record['wins']
        t.losses = record['losses']
        db.session.add(t)
    db.session.commit()

def main():
    with app.app_context():
        records = get_records()
        write_records_to_db(records)
        for day in YESTERDAY, TODAY:
            scores = get_scores(day)
            write_scores_to_file(day, scores)
            write_to_db(day, scores)
        save_timestamp()


if __name__ == '__main__':
    main()
