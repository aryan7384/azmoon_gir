from flask import Blueprint, request, url_for, redirect, session, flash, render_template
from apps.users.models import *
from apps.database import db
from apps.admin.forms import *
from ..extensions import hashing
from hashlib import sha256
import os
import dotenv

dotenv.load_dotenv()

blueprint = Blueprint('admin', __name__)


@blueprint.route("/admin/")
def admin_homepage():
    if session.get("admin_logged_in") != True:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    return render_template("admin/admin.html")


@blueprint.route("/admin/login/", methods=["GET", "POST"])
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
    if session.get("admin_logged_in") != True:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    teachers = []
    teachers_record = Teacher.query.all()

    for teacher in teachers_record:
        teacher_dict = {"username": teacher.username,
                        "students": User.query.where(
                            User.teacher_id == teacher.id
                        ).all()[:3],
                        "id": teacher.id}
        teachers.append(teacher_dict)
        

    return render_template("admin/manage-teachers.html",
                           teachers=teachers)


@blueprint.route("/admin/register-teacher", methods=["GET", "POST"])
def registerTeacher():
    if session.get("admin_logged_in") != True:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    form = RegisterTeacherForm()
    if form.validate_on_submit():
        new_teacher = Teacher(username=form.username.data,
                              password=hashing.hash_value(
                                  form.password.data,
                                  salt=os.getenv("SALT")
                              ))
        
        db.session.add(new_teacher)
        db.session.commit()

        flash("معلم جدید ثبت شد!")
        return redirect(url_for("admin.admin_homepage"))

    return render_template("admin/register-teacher.html",
                           form=form)


@blueprint.route("/admin/remove-teacher")
def removeTeacher():
    flash("not implemented")
    return redirect(url_for('admin.admin_homepage'))


@blueprint.route("/admin/modify-teacher")
def modifyTeacher():
    flash("not implemented")
    return redirect(url_for('admin.admin_homepage'))
