from flask import Blueprint, request, url_for, redirect, session, flash, render_template
from apps.users.models import User, Azmoon, RealQuestion, RealOption
from apps.database import db
from apps.admin.forms import *
from ..extensions import hashing
from hashlib import sha256
import os
import dotenv

dotenv.load_dotenv()

blueprint = Blueprint('admin', __name__)
get_post = ['GET', 'POST']


@blueprint.route("/admin/")
def admin_homepage():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    return render_template("admin/admin.html")


@blueprint.route("/admin/login/", methods=get_post)
def login():
    form = LoginForm()
    if form.validate_on_submit():

        if sha256(request.form["password"].encode()).hexdigest() == os.getenv("ADMIN_PASSWORD_HASHED"):
            flash("خوش آمدید!")
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_homepage'))
        
        flash("رمز اشتباه")

    return render_template("admin/login.html", form=form)


@blueprint.route("/admin/manage-teachers")
def manageTeachers():
    return render_template("admin/manage-teachers.html")