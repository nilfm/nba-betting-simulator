#!/usr/bin/env python3

import json
from datetime import datetime, timedelta
from pprint import pprint
from app import app, db, api
from app.forms import *
from app.models import *
from app.email import *
from flask import render_template, jsonify, flash, redirect, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
import subprocess


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    return render_template("index.html")


@app.route("/explained")
def explained():
    return render_template("explained.html", title="What is this?")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, funds=1000)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Successfully registered user {user.username}")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash("Check your email for instructions to reset your password")
        return redirect(url_for("login"))
    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    # Cause 404 if user does not exist
    user = User.query.filter_by(username=username).first_or_404()
    return render_template(
        "user.html", title=f"{username}'s profile", username=username
    )


@app.route("/ranking")
def ranking():
    return render_template("ranking.html", title="Ranking")


@app.route("/reset_account", methods=["POST"])
@login_required
def reset_account():
    current_user.reset_account()
    flash("Your account has been reset")
    return redirect(url_for("index"))


@app.route("/delete_account", methods=["POST"])
@login_required
def delete_account():
    id = current_user.id
    logout_user()
    User.query.filter_by(id=id).delete()
    Bet.query.filter_by(user_id=id).delete()
    db.session.commit()
    return redirect(url_for("login"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if current_user.username != "nilfm":
        return redirect(url_for("index"))
    last_games = TimestampGames.query.order_by(TimestampGames.timestamp.desc()).first()
    last_scores = TimestampScores.query.order_by(
        TimestampScores.timestamp.desc()
    ).first()
    return render_template("admin.html", last_games=last_games, last_scores=last_scores)


@app.route("/execute/<name>", methods=["POST"])
@login_required
def execute(name):
    if current_user.username != "nilfm":
        return redirect(url_for("index"))
    subprocess.call(f"./{name}", shell=True)
    flash(f"Script {name} called")
    return redirect(url_for("admin"))


@app.before_request
def before_request():
    if current_user.is_authenticated:
        g.search_form = SearchForm()


@app.route("/search")
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for("index"))
    users, total = User.search(g.search_form.q.data.lower(), 5)
    return render_template("search.html", title="Search", users=users, total=len(users))


@app.route("/feed")
@login_required
def feed():
    return render_template("feed.html", title="Feed")
