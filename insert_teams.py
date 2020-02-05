#!/usr/bin/env python3

import json
from app import db
from app.models import Team

IN_FILE_PATH = "teams.json"


def main():
    with open(IN_FILE_PATH, "r") as infile:
        teams = json.load(infile)

    for team in teams:
        t = Team(short_name=team["short_name"], long_name=team["team_name"])
        print(t)
        try:
            db.session.add(t)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()


if __name__ == "__main__":
    main()
