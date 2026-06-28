from flask import Blueprint, request, url_for, redirect, session, flash, render_template
from apps.users.models import *
from apps.database import db
from apps.admin.forms import *
from ..extensions import hashing
from hashlib import sha256
import os
import dotenv
import secrets

dotenv.load_dotenv()

blueprint = Blueprint('admin', __name__)


@blueprint.route("/admin/")
def admin_homepage():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    if session["admin_logged_in"]:
        session['csrf_token'] = secrets.token_urlsafe(32)
        return render_template("admin/admin.html",
                               csrf_token=session["csrf_token"])
    
    else:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))


@blueprint.route("/admin/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if sha256(request.form["password"].encode("utf-8")).hexdigest() == os.getenv("ADMIN_PASSWORD_HASHED"):
            flash("خوش آمدید!")
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_homepage'))
        
        else:
            flash("رمز اشتباه")
            return render_template("admin/login.html", form=form)

    return render_template("admin/login.html", form=form)


@blueprint.route("/admin/manage-teachers")
def manage_teachers():
    if session.get("admin_logged_in") != True:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    teachers = []
    teachers_record = Teacher.query.all()

    for teacher in teachers_record:
        students = User.query.where(
                            User.teacher_id == teacher.id
                        ).all()[:3]
        students = set(map(lambda s: s.name, students))
        teacher_dict = {"username": teacher.username,
                        "students": students,
                        "id": teacher.id,
                        "limit": teacher.student_limit}
        teachers.append(teacher_dict)


    # generating csrf_token
    session['csrf_token'] = secrets.token_urlsafe(32)
    return render_template("admin/manage-teachers.html",
                           teachers=teachers,
                           len=len,
                           csrf_token=session['csrf_token'])


@blueprint.route("/admin/register-teacher", methods=["GET", "POST"])
def register_teacher():
    if session.get("admin_logged_in") != True:
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    form = RegisterTeacherForm()
    if form.validate_on_submit():
        new_teacher = Teacher(username=form.username.data,
                              password=hashing.hash_value(
                                  form.password.data,
                                  salt=os.getenv("SALT")
                              ),
                              student_limit=form.limit.data)
        
        db.session.add(new_teacher)
        db.session.commit()

        flash("معلم جدید ثبت شد!")
        return redirect(url_for("admin.manage_teachers"))

    return render_template("admin/register-teacher.html",
                           form=form)


@blueprint.route("/admin/remove-teacher/<teacher_id>", methods=["POST"])
def remove_teacher(teacher_id):
    if not (session.get("admin_logged_in") == True):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))

    if session.get("csrf_token") != request.form["csrf_token"]:
        flash("CSRF تایید نشد.")
        return redirect(url_for('admin.admin_homepage'))

    teacher = Teacher.query.filter_by(id=teacher_id).first()
    users = User.query.filter_by(teacher_id=teacher.id).all()
    for user in users:
        DescAnswer.query.filter_by(student_id=user.id).delete()
        db.session.delete(user)

    exams = Azmoon.query.filter_by(teacher_id=teacher.id).all()
    for exam in exams:
        db.session.delete(exam)
        
    db.session.delete(teacher)
    db.session.commit()

    flash("معلم حذف شد.")
    return redirect(url_for("admin.manage_teachers"))


@blueprint.route("/admin/modify_teacher/<teacher_id>", methods=["POST"])
def modify_teacher(teacher_id):
    if not (session.get("admin_logged_in") == True):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))

    if session.get("csrf_token") != request.form["csrf_token"]:
        flash("CSRF تایید نشد.")
        return redirect(url_for('admin.admin_homepage'))

    teacher = Teacher.query.filter_by(id=teacher_id).first()
    try:
        teacher.student_limit = int(request.form["limit"])
        db.session.commit()

    except:
        flash("مقدار وارد شده نامعتبر است.")
        return redirect(url_for("admin.manage_teachers"))
        
    flash("سقف مجاز دانش اموز ها تغییر یافت.")
    return redirect(url_for("admin.manage_teachers"))

@blueprint.route("/admin/logout", methods=["POST"])
def logout():
    if not (session.get("admin_logged_in") == True):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))

    if session.get("csrf_token") != request.form["csrf_token"]:
        flash("CSRF تایید نشد.")
        return redirect(url_for('admin.admin_homepage'))
    
    del session["admin_logged_in"]
    flash("یا موفقیت خارج شدید")
    return redirect(url_for("home.home"))
