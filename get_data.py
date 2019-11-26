#!/usr/bin/env python3

import requests
import json
from datetime import datetime
import os

API_KEY = "bb3a24a9d37b206d8324f4aecc19e82c"
URL = f"https://api.the-odds-api.com/v3/odds/?apiKey={API_KEY}&sport=basketball_nba&region=us&mkt=h2h"
TODAY = datetime.now().strftime('%Y-%m-%d')
OUT_FILE_PATH = f"raw_{TODAY}.txt"
OUT_DIR = "raw"

def get():
    r = requests.get(URL)
    return r.json()
    
def write_to_file():
    data = get()
    with open(os.path.join(OUT_DIR, OUT_FILE_PATH), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    
def main():
    write_to_file()

if __name__ == '__main__':
    main()
