from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm
from app.labels import DASHBOARD_ENDPOINTS
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    return redirect(url_for(DASHBOARD_ENDPOINTS[current_user.role]))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalars(db.select(User).where(User.email == email)).first()
        if user is None or not user.is_active or not user.check_password(form.password.data):
            flash("The username or password is incorrect.", "danger")
        else:
            login_user(user)
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//") and urlparse(next_url).netloc == "":
                return redirect(next_url)
            return redirect(url_for(DASHBOARD_ENDPOINTS[user.role]))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have signed out.", "info")
    return redirect(url_for("auth.login"))
