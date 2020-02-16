#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from app import app, db, api
from app.models import *
from flask import jsonify, request
from flask_login import current_user, login_required


def custom_key(x):
    """
    Used for sorting purposes, for the autocomplete method

    Input: a dictionary of the form:
    {
        'value': <username>,
        'data': 
        {
            'category': < Me | Following | Not Following >
        }
    }

    Output: a pair of the form: (< 0 | 1 | 2 >, username), where the first 
            value is 0 if 'Me', 1 if 'Following', 2 if 'Not Following'
    """
    mapping = {"Me": 0, "Following": 1, "Not Following": 2}
    return mapping[x["data"]["category"]], x["value"]


@api.route("/users", methods=["GET"])
@login_required
def api_users():
    """
    Fetches the necessary data for autocomplete.
    
    Returns a list of objects of the form:
    {
        'value': <username>,
        'data': 
        {
            'category': < Me | Following | Not Following >
        }
    }
    
    This list is sorted so that 'Me' appears first, then 'Following' and 
    then 'Not Following'. In case of a tie, alphabetical ordering on 
    usernames is used to sort.
    """
    if not current_user.is_authenticated:
        return jsonify(None)
    users = User.query.all()
    params = [
        {
            "value": u.username,
            "data": {
                "category": "Following"
                if current_user.is_following(u)
                else "Me"
                if current_user.id == u.id
                else "Not Following"
            },
        }
        for u in users
    ]
    params = sorted(params, key=custom_key)
    return jsonify(params)


@api.route("/user/<username>", methods=["GET"])
@login_required
def api_user(username):
    """
    Returns:
        -Information about the user:
            id
            username
            funds
            ranking_funds
        -Information relating current user and this user:
            is_following
            is_current
        -List of stats, which contains:
            won: number of won bets
            lost: number of lost bets
            pending: number of pending bets
            finished: number of finished bets (won+lost)
            by_team: [
                {
                    short_name
                    long_name
                    bet_for {
                        total_balance
                        num_wins
                        num_losses
                        num_bets
                    }
                    bet_against {
                        total_balance
                        num_wins
                        num_losses
                        num_bets
                    }
                    total {
                        total_balance
                        num_wins
                        num_losses
                        num_bets
                    }
                }
            ]
        -List of pending bets
    """
    user = User.query.filter_by(username=username).first_or_404()
    bets = Bet.query.filter_by(user_id=user.id).all()
    pending_bets = [bet for bet in bets if not bet.finished]
    finished_bets = [bet for bet in bets if bet.finished]
    num_finished = len(finished_bets)
    num_pending = len(pending_bets)
    num_won = sum(bet.won for bet in finished_bets)
    team_stats = user.stats_by_team()
    data = {
        "is_following": current_user.is_following(user),
        "is_current": current_user.id == user.id,
        "stats": {
            "finished": num_finished,
            "won": num_won,
            "lost": num_finished - num_won,
            "pending": num_pending,
            "by_team": team_stats,
        },
        "pending_bets": [bet.to_dict() for bet in pending_bets],
    }
    data.update(user.to_dict())
    return jsonify(data)


@api.route("/user/<username>/bets")
@login_required
def api_user_bets(username):
    """
    Returns an object with:
        -success: BOOLEAN
        -msg: STRING
        -complete: BOOLEAN
        -data: Array of days, each with an array of bets
    """
    try:
        page = int(request.args.get("page", 0))
        page_length = 3
    except ValueError:
        response = {
            "success": False,
            "complete": True,
            "msg": "Bad request: missing necessary fields",
            "data": {},
        }
        return jsonify(response)

    user = User.query.filter_by(username=username).first_or_404()
    finished_bets = Bet.query.filter_by(user_id=user.id, finished=True).all()

    days = sorted(set(bet.game.date for bet in finished_bets), reverse=True)
    bets_days = [
        {
            "day": day,
            "bets": [bet.to_dict() for bet in finished_bets if bet.game.date == day],
        }
        for day in days
    ]
    days_in_page = bets_days[page : page + page_length]
    response = {
        "success": True,
        "complete": page + page_length >= len(bets_days),
        "msg": "OK",
        "data": days_in_page,
    }
    return response


@api.route("/current_user", methods=["GET"])
def api_current_user():
    """
    Returns an object with:
        -is_authenticated: BOOLEAN
        -data: If not is_authenticated, returns None. 
               Otherwise, an object containing the current user's data.
    """
    data = {
        "is_authenticated": current_user.is_authenticated,
        "data": None if not current_user.is_authenticated else current_user.to_dict(),
    }
    return jsonify(data)


@api.route("/feed", methods=["GET"])
@login_required
def api_feed():
    """
    Returns an object with:
        -success: BOOLEAN
        -msg: STRING
        -complete: BOOLEAN
        -data: Array of days, each with an array of games, each with an array of bets
    """
    try:
        page = int(request.args.get("page", 0))
        page_length = 3
    except ValueError:
        response = {
            "success": False,
            "complete": True,
            "msg": "Bad request: missing necessary fields",
            "data": {},
        }
        return jsonify(response)

    bets = Bet.query.order_by(Bet.date_time.desc()).all()
    followed_bets = [
        b for b in bets if current_user.is_following(b.user) or current_user == b.user
    ]
    days = sorted(set(b.game.date for b in followed_bets), reverse=True)

    # First calculate in dictionary format for linear complexity
    bets_days = {day: {} for day in days}
    for bet in followed_bets:
        if bet.game_id not in bets_days[bet.game.date]:
            bets_days[bet.game.date][bet.game_id] = {
                "info": bet.game.to_dict(),
                "bets": [],
            }
        bets_days[bet.game.date][bet.game_id]["bets"].append(bet.to_dict())

    # For simplicity and ability to sort:
    #    Convert dictionary mapping day to games into array of days
    #    Convert dictionaries mapping game_id to game into array of games
    to_return = [
        {"day": day, "games": [bets_days[day][game] for game in games]}
        for day, games in bets_days.items()
    ]

    days_in_page = to_return[page : page + page_length]
    response = {
        "success": True,
        "complete": page + page_length >= len(to_return),
        "msg": "OK",
        "data": days_in_page,
    }
    return jsonify(response)


@api.route("/ranking/global", methods=["GET"])
def api_ranking_global():
    """
    Returns an object with:
        -success: BOOLEAN
        -msg: STRING
        -complete: BOOLEAN
        -data: Dictionary that contains an array of names
    """
    try:
        page = int(request.args.get("page", 0))
        page_length = 10
    except ValueError:
        response = {
            "success": False,
            "complete": True,
            "msg": "Bad request: missing necessary fields",
            "data": {},
        }
        return jsonify(response)

    users = User.query.order_by(User.ranking_funds.desc()).all()
    users = [u.to_dict() for u in users]
    users_page = users[page : page + page_length]

    response = {
        "success": True,
        "msg": "OK",
        "complete": page + page_length >= len(users),
        "data": {"ranking": users_page,},
    }
    return jsonify(response)


@api.route("/ranking/followed", methods=["GET"])
@login_required
def api_ranking_followed():
    """
    Returns an object with:
        -success: BOOLEAN
        -msg: STRING
        -complete: BOOLEAN
        -data: Dictionary that contains an array of names
    """
    if not current_user.is_authenticated:
        response = {
            "success": False,
            "msg": "Current user is not authenticated",
            "complete": True,
            "data": {},
        }
        return jsonify(response)

    try:
        page = int(request.args.get("page", 0))
        page_length = 10
    except ValueError:
        response = {
            "success": False,
            "complete": True,
            "msg": "Bad request: missing necessary fields",
            "data": {},
        }
        return jsonify(response)

    followed = current_user.followed_users()
    followed = [u.to_dict() for u in followed]
    followed_page = followed[page : page + page_length]

    response = {
        "success": True,
        "msg": "OK",
        "complete": page + page_length >= len(followed),
        "data": {"ranking": followed_page,},
    }
    return jsonify(response)


@api.route("/current_rank", methods=["GET"])
def api_current_rank():
    """
    Returns an object of the form:
    {
        'rank_global': rank of the current user in the global ranking
        'rank_followed': rank of the current user in the followed ranking
    }
    
    If the current user is not logged in, both fields are -1.
    """
    if not current_user.is_authenticated:
        response = {"rank_global": -1, "rank_followed": -1}
        return jsonify(response)

    users = User.query.order_by(User.ranking_funds.desc()).all()
    followed = current_user.followed_users()

    rank_global = -1
    for i, user in enumerate(users, start=1):
        if user.id == current_user.id:
            rank_global = i
            break

    rank_followed = -1
    for i, user in enumerate(followed, start=1):
        if user.id == current_user.id:
            rank_followed = i
            break

    response = {"rank_global": rank_global, "rank_followed": rank_followed}
    return jsonify(response)


@api.route("/games", methods=["GET"])
@login_required
def api_games_today():
    """
    Returns an array of games. Each game is of the following form:
    {
        'game_id': <game_id>
        'home_team': {
            'short':  <3-letter abbreviation>
            'long':   <full name>
            'odds':   <decimal number>
            'score':  <team's score if the game is finished, else None>
            'wins':   <team's number of won games so far this season>
            'losses': <team's number of lost games so far this season>
        },
        'away_team': {
            'short':  <3-letter abbreviation>
            'long':   <full name>
            'odds':   <decimal number>
            'score':  <team's score if the game is finished, else None>
            'wins':   <team's number of won games so far this season>
            'losses': <team's number of lost games so far this season>
        },
        'finished':  <boolean that tells if the game is finished>
        'winner':    <1 if home team won, 2 if away team won, None if unfinished>
        'date_time': <start date and time in format 'YYYY-MM-DD hh:mm:ss'>
        'date':      <start date in format 'YYYY-MM-DD'>
        'already_bet_home': <boolean that tells if current user has already bet on home team>
        'already_bet_away': <boolean that tells if current user has already bet on away team>
    }
    """
    TODAY = (datetime.utcnow() - timedelta(hours=8)).strftime("%Y-%m-%d")
    games = Game.query.filter_by(date=TODAY).all()
    already_bet_home = [
        Bet.query.filter_by(
            game_id=g.id, user_id=current_user.id, bet_on_home=True
        ).first()
        is not None
        for g in games
    ]
    already_bet_away = [
        Bet.query.filter_by(
            game_id=g.id, user_id=current_user.id, bet_on_home=False
        ).first()
        is not None
        for g in games
    ]
    games = [g.to_dict() for g in games]
    for game, home, away in zip(games, already_bet_home, already_bet_away):
        game["already_bet_home"] = home
        game["already_bet_away"] = away
    return jsonify(games)


@api.route("/place_bet", methods=["POST"])
@login_required
def api_place_bet():
    """
    Expected data:
    {
        'game_id': INTEGER,
        'bet_on_home': BOOLEAN,
        'amount': INTEGER
    }
    where:
        -game_id is a valid game id for a game that hasn't started
        -amount is between 1 and current funds 
        -the user has not yet bet on this team for this game
        
    Returns:
    {
        'success': BOOLEAN,
        'msg': STRING
    }    
    where:
        -success is true if the bet has been placed successfully
        -msg is one of:
            -"You have successfully bet X coins on Y [team]"
            -"This game already started"
            -"This game doesn't exist"
            -"The bet amount has to be positive"
            -"You only have X coins"
            -"You have already bet on this game"
            -"Bad request: missing necessary fields"
    """
    data = json.loads(request.get_data())
    if "game_id" not in data or "amount" not in data or "bet_on_home" not in data:
        return {"success": False, "msg": "Bad request: missing necessary fields"}
    response = current_user.place_bet(
        data["game_id"], data["amount"], data["bet_on_home"]
    )
    return jsonify(response)


@api.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username):
    """
    Expected data: None

    Returns:
    {
        'success': BOOLEAN,
        'msg': STRING
    }    
    where:
        -success is true if the user has been followed successfully
        -msg is one of:
            -"You are now following X
            -"User not found"
            -"You cannot follow yourself"
            -"You were already following X"
    """
    user = User.query.filter_by(username=username).first()
    response = current_user.follow(user)
    return jsonify(response)


@api.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username):
    """
    Expected data: None

    Returns:
    {
        'success': BOOLEAN,
        'msg': STRING
    }    
    where:
        -success is true if the user has been unfollowed successfully
        -msg is one of:
            -"You are no longer following X
            -"User not found"
            -"You cannot unfollow yourself"
            -"You were already not following X"
    """
    user = User.query.filter_by(username=username).first()
    response = current_user.unfollow(user)
    return jsonify(response)
