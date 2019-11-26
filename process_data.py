#!/usr/bin/env python3

import json
import pprint
from datetime import datetime
import os

TODAY = datetime.now().strftime('%Y-%m-%d')
IN_FILE_PATH = f"raw_{TODAY}.txt"
OUT_FILE_PATH = f"data_{TODAY}.txt"
IN_DIR = "raw"
OUT_DIR = "data"

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
    good_data = [process(game) for game in data["data"]]
    return good_data

def write_to_file():
    with open(os.path.join(IN_DIR, IN_FILE_PATH), 'r') as infile:
        data = json.load(infile)
    
    processed_data = process_data(data)
    
    with open(os.path.join(OUT_DIR, OUT_FILE_PATH), 'w') as outfile:
        json.dump(processed_data, outfile, indent=4)

def main():
    write_to_file()

if __name__ == '__main__':
    main()
