from flask import Blueprint, request, url_for, redirect, session, flash, render_template
from apps.users.models import User, Azmoon, RealQuestion, RealOption
from apps.database import db
from apps.admin.forms import *
from ..extensions import hashing
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
        if request.form["password"] == "1234":
            flash("خوش آمدید!")
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin_homepage'))
        flash("رمز اشتباه")

    return render_template("admin/login.html", form=form)


@blueprint.route("/admin/register-user/", methods=get_post)
def register_new_user():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    form = RegisterUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=hashing.hash_value(form.username.data+"!", salt=os.getenv("SALT")))

        db.session.add(user)
        db.session.commit()
        flash(f"نام کاربری {form.username.data} ساخته شد.")
        return redirect(url_for('admin.admin_homepage'))

    return render_template("admin/register-user.html", form=form)


@blueprint.route("/admin/azmoon/register/", methods=get_post)
def azmoon_register():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    form = RegisterAzmoonForm()

    if form.validate_on_submit():
        azmoon = Azmoon(name=form.name.data)
        db.session.add(azmoon)
        db.session.commit()
        users = form.users.data.strip().split(os.linesep)

        for user in users:
            user_record = User.query.filter_by(username=user).first()
            user_record.azmoon_id = azmoon.id
            user_record.answered = False
            db.session.commit()
        
        flash(f"آزمون {azmoon.name} با موفقیت ساخته شد.")
        return redirect(url_for('admin.admin_homepage'))

    return render_template("admin/register-azmoon.html", form=form)


@blueprint.route("/admin/azmoon/add_questions/", methods=get_post)
def add_questions():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    q_form = SubmitQuestionForm()

    if q_form.validate_on_submit():
        azmoon = Azmoon.query.filter_by(name=q_form.azmoon_name.data).first()
        new_question = RealQuestion(title=q_form.text.data, azmoon_id=azmoon.id)
        db.session.add(new_question)
        db.session.commit()

        no_answer_option = RealOption(question_id=new_question.id,
                                      text="بدون پاسخ")
        db.session.add(no_answer_option)
        db.session.commit()
        
        flash(f"سوال ثبت شد. ID سوال: {new_question.id}")
        return redirect(url_for('admin.admin_homepage'))

    return render_template("admin/register-question.html", form=q_form)


@blueprint.route("/admin/azmoon/add_options/", methods=get_post)
def add_options():
    if not session.get("admin_logged_in"):
        flash("اول رمز عبور را وارد کنید.")
        return redirect(url_for('admin.login'))
    
    op_form = SubmitOptionForm()
    if op_form.validate_on_submit():
        question = RealQuestion.query.filter_by(id=op_form.question_id.data).first()
        option = RealOption(text=op_form.text.data,
                            question_id=question.id,
                            is_correct=op_form.is_correct.data)
        
        db.session.add(option)
        db.session.commit()
        flash(f"گزینه برای سوال {question.id} ثبت شد.")
        return redirect(url_for('admin.admin_homepage'))

    return render_template("admin/register-option.html", form=op_form)