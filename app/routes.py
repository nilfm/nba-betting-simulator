from app import app
from flask import render_template
import json

IN_FILE_PATH = "../data/data_2019-11-25.txt"

@app.route('/')
@app.route('/index')
def index():
    with open(IN_FILE_PATH, 'r') as infile:
        games = json.load(infile)
    return render_template('index.html', games=games)
