from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .forms import *
from ..database import db
from apps.users.models import *
from ..extensions import *
import os
import dotenv

dotenv.load_dotenv()

blueprint = Blueprint('teachers', __name__)


@blueprint.route("/teacher/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        hashed_password = hashing.hash_value(form.password.data, salt=os.getenv("SALT"))
        if Teacher.query.filter_by(username=form.username.data,
                                   password=hashed_password).first():
            session['teacher_username'] = form.username.data
            return redirect(url_for('teachers.dashboard'))

        flash("نام کاربری یا رمز عبور اشتباه است.")
        return render_template("teachers/login.html", form=form)

    return render_template("teachers/login.html", form=form)


@blueprint.route("/teacher")
def dashboard():
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if not teacher:
        flash("لطفا مجدد وارد شوید", "info")
        del session['teacher_username']
        return redirect(url_for('teachers.login'))

    exams = Azmoon.query.filter_by(teacher_id=teacher.id).all()
    return render_template("teachers/teacher-panel.html",
                           exams=exams)


@blueprint.route("/teacher/azmoon/register", methods=['GET', 'POST'])
def register_azmoon():
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if not teacher:
        flash("لطفا مجدد وارد شوید", "info")
        del session['teacher_username']
        return redirect(url_for('teachers.login'))

    form = RegisterExamForm()
    if form.validate_on_submit():
        users = form.users.data.strip().splitlines()
        for i in users:
            user = User.query.where(teacher_id=teacher.id,
                                    username=i).first()
            if not user:
                flash(f"کاربر {i} برای معلم دیگری ثبت شده.")
                return redirect(url_for('teachers.register_azmoon'))
        azmoon = Azmoon(teacher_id=teacher.id,
                        name=form.azmoon_name.data,
                        is_available=False)
        db.session.add(azmoon)
        db.session.commit()
        print(users)
        if len(users) != 0:
            for user in users:
                new_user = User.query.where(username=user).first()
                new_user.azmoon_id = azmoon.id
                db.session.add(new_user)
                db.session.commit()

        flash("آزمون جدید ثبت شد.")
        return redirect(url_for("teachers.dashboard"))

    return render_template("teachers/register-exam.html",
                           form=form)


@blueprint.route("/teacher/azmoon/delete/<id>", methods=['POST'])
def delete_azmoon(id):
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if not teacher:
        flash("لطفا مجدد وارد شوید", "info")
        del session['teacher_username']
        return redirect(url_for('teachers.login'))

    azmoon = Azmoon.query.filter_by(id=id).first()
    if azmoon.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید.")
        return redirect(url_for('teachers.dashboard'))

    db.session.delete(azmoon)
    db.session.commit()
    flash(f"آزمون {azmoon.name}با موفقیت حذف شد.")
    return redirect(url_for('teachers.dashboard'))


@blueprint.route("/teacher/azmoon/modify/<id>", methods=['GET', 'POST'])
def modify_azmoon(id):
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if not teacher:
        flash("لطفا مجدد وارد شوید", "info")
        del session['teacher_username']
        return redirect(url_for('teachers.login'))

    exam = Azmoon.query.where(Azmoon.id == id).first()
    if not exam:
        flash("آزمون یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    if exam.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید")
        return redirect(url_for('teachers.dashboard'))

    form = ModifyExamForm()
    if form.validate_on_submit():
        exam.name = form.azmoon_name.data
        users_records = User.query.filter_by(azmoon_id=exam.id).all()
        for user in users_records:
            user.azmoon_id = None
            db.session.add(user)
        db.session.commit()

        users = form.users.data.strip().splitlines()
        for user in users:
            user_record = User.query.filter_by(username=user).first()
            if user_record.teacher_id != teacher.id:
                flash(f"کاربر {user_record.username}برای شما ثبت نشده است.")
                return redirect(url_for('teachers.modify_azmoon', id=id))
            user_record.azmoon_id = exam.id
            db.session.add(user_record)
        db.session.commit()

        flash("ازمون با موفقیت به روزرسانی شد.")
        return redirect(url_for('teachers.dashboard'))

    form.azmoon_name = exam.name
    users_records = User.query.filter_by(azmoon_id=exam.id).all()
    users = []
    for i in users_records:
        users.append(i.username)
    form.users = os.linesep.join(users)
    return render_template("teachers/modify_exam.html", form=form)


