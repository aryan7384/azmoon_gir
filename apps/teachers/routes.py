from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .forms import *
from ..database import db
from apps.users.models import *
from ..extensions import *
import os
import dotenv

dotenv.load_dotenv()

blueprint = Blueprint('teachers', __name__)


@blueprint.route("/teacher/login")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        hashed_password = hashing.hash_value(form.password.data, salt=os.getenv("SALT"))
        if Teacher.query.filter_by(username=form.username.data,
                                   password=hashed_password).first():
            session['teacher_username'] = form.username.data
            flash(f"خوش امدید {form.username.data}", "info")
            return redirect(url_for('teachers.dashboard'))

        flash("نام کاربری یا رمز عبور اشتباه است.")
        return render_template("teachers/login.html", form=form)

    return render_template("teachers/login.html", form=form)


@blueprint.route("/teacher/dashboard")
def dashboard():
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))
    return "<p>خوژتیپ</p>"
