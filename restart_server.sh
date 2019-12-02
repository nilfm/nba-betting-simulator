#!/usr/bin/env bash

cd /root/nba-betting-simulator
source my_env/bin/activate
pkill gunicorn 
my_env/bin/gunicorn -c /etc/gunicorn.conf.py wsgi:app --daemon

