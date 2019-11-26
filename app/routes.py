#!/usr/bin/env python3

from app import app
from app.forms import LoginForm
from flask import render_template, flash, redirect, url_for
import json
from datetime import datetime

TODAY = datetime.now().strftime('%Y-%m-%d')
IN_FILE_PATH = f"../data/data_{TODAY}.txt"

@app.route('/')
@app.route('/index')
def index():
    with open(IN_FILE_PATH, 'r') as infile:
        games = json.load(infile)
    print(games)
    return render_template('index.html', games=games)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)
