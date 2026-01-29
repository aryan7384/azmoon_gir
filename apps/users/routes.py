from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from .forms import *
from ..database import db
from .models import *
from ..extensions import *
import os
import secrets
import dotenv

dotenv.load_dotenv()

blueprint = Blueprint('users', __name__)


def get_email(username):
    user = get_user(username)
    return user.email


def get_user(username):
    return User.query.filter_by(username=username).first()


def calculate_result(user):
    user_azmoon = Azmoon.query.filter_by(id=user.azmoon_id).first()
    questions = RealQuestion.query.filter_by(azmoon_id=user_azmoon.id).all()
    total_questions = len(questions)

    user_answers = [Answer.query.filter_by(for_student=user.id, for_question=i.id).first() for i in questions]

    score = 0
    for answer in user_answers:
        if answer is None:
            continue
        selected_option = answer.answer
        true_answer = RealOption.query.where(
            RealOption.question_id == answer.for_question,
            RealOption.is_correct == True
        ).first()

        if selected_option == true_answer.id:
            score += 100 / total_questions
        
        else:
            score -= (33.33 / total_questions) 

    New_result = Result(for_student=user.id,
                        for_azmoon_name=user_azmoon.name,
                        percent=score)

    db.session.add(New_result)
    db.session.commit()
    

@blueprint.route('/login/', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        hashed_password = hashing.hash_value(form.password.data, salt=os.getenv("SALT"))

        select_ = db.session.query(User).where(User.username == form.username.data,
                                               User.password == hashed_password)

        if db.session.execute(select_).scalar():
            flash(f"خوش آمدید {form.username.data}", "success")
            if form.remember_me.data:
                session.permanent = True
            session['username'] = form.username.data
            return redirect(url_for('users.dashboard'))

        flash(f"نام کاربری یا رمز عبور اشتباه است", "danger")
        return render_template("users/login.html", form=form)
    return render_template("users/login.html", form=form)


@blueprint.route('/dashboard/', methods=["GET", "POST"])
def dashboard():
    username = session.get("username")
    if not username:
        flash("لطفا وارد حساب کاربری شوید.", "info")
        return redirect(url_for('home.home'))

    if not get_user(username):
        flash("لطفا مجدد وارد شوید.", "info")
        session.clear()
        return redirect(url_for('users.login'))

    update_profile_form = UpdateProfileForm()

    if update_profile_form.validate_on_submit():
        if db.session.query(User).filter(User.email == update_profile_form.email.data,
                                         User.email != get_email(session['username'])).count():
            flash("ایمیل تکراری است. ایمیل دیگری را امتحان کنید.", "warning")
            return render_template("users/dashboard.html", form=update_profile_form)

        user = get_user(username)
        if user.email != update_profile_form.email.data:
            user.email = update_profile_form.email.data

        session['username'] = user.username
        db.session.commit()

        flash("اکانت با موفقیت بروزرسانی شد.", "success")
        return redirect(url_for("users.dashboard"))

    elif request.method == "GET":
        update_profile_form.email.data = get_user(session['username']).email

    return render_template("users/dashboard.html",
                           username=session['username'],
                           form=update_profile_form)


@blueprint.route('/logout/')
def logout():
    username = session.get("username")
    if not username:
        flash("لطفا وارد حساب کاربری شوید.", "info")
        return redirect(url_for('home.home'))

    if not get_user(username):
        flash("لطفا دوباره وارد شوید.", "info")
        session.clear()
        return redirect(url_for('users.login'))

    session.permanent = False
    session.clear()
    flash("با موفقیت خارج شدید.", "success")
    return redirect(url_for("users.login"))


@blueprint.route('/updatepassword/', methods=["GET", "POST"])
def update_password():
    username = session.get("username")
    if not username:
        flash("لطفا وارد شوید", "info")
        return redirect(url_for('home.home'))

    if not get_user(username):
        flash("لطفا دوباره وارد شوید.", "info")
        session.clear()
        return redirect(url_for('users.login'))

    update_password_form = UpdatePasswordForm()
    if update_password_form.validate_on_submit():
        if not bool(User.query.filter(User.username == username,
                                      User.password == hashing.hash_value(
                                          update_password_form.old_password.data, salt="thisiselonmusk"
                                      )).count()):
            flash("رمز اشتباه است", "danger")
            return render_template("users/update_password.html", form=update_password_form)
        hashed_password = hashing.hash_value(update_password_form.new_password.data,
                                             salt="thisiselonmusk")
        user = get_user(username)
        user.password = hashed_password
        db.session.commit()
        flash("رمز عبور بروزرسانی شد", "success")
        return redirect(url_for("users.dashboard"))
    return render_template('users/update_password.html', form=update_password_form)


@blueprint.route("/forgot-password/", methods=["GET", "POST"])
def forgot_password():
    form = PasswordResetForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        if user := User.query.filter(User.username == username,
                                     User.email == email).first():
            user.password = hashing.hash_value("123456", salt=os.getenv("SALT"))
            # user.password = hashing.hash_value(password := str(random.randint(10000000, 99999999)))
            # send_new_password(password)
            db.session.commit()
            flash("رمز حساب کاربری به 123456 تغییر داده شد. بعد از ورود به حساب کاربری حتما ان را تغییر دهید.",
                  "success")
            # flash("new password has been sent to the account's phone number.")
            return redirect(url_for("users.login"))
        flash("ایمیل و نام کاربری مربوط به یک حساب مشترک نیستند.", "danger")
        return redirect(url_for("users.forgot_password"))

    return render_template("users/forgot_password.html", form=form)


@blueprint.route("/azmoon/", methods=["GET", "POST"])
def azmoon():
    username = session.get("username")
    if not username:
        flash("لطفا وارد شوید.", "info")
        return redirect(url_for('users.login'))

    if not get_user(username):
        session.clear()
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    has_exam = (get_user(username).azmoon_id != 0) and not get_user(username).answered
    return render_template("users/azmoon/entry_page.html",
                           username=username, has_exam=has_exam,
                           Azmoon=Azmoon,
                           get_user=get_user)


@blueprint.route("/start-exam/", methods=["GET", "POST"])
def start_exam():
    user = get_user(session.get("username"))
    if not user:
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    if user.answered:
        flash("نمیتوانید مجدد به آزمون پاسخ دهید.", "warning")
        return redirect(url_for("users.dashboard"))

    exam = Azmoon.query.filter_by(id=user.azmoon_id).first()
    if request.method == 'POST':

        if request.form.get("csrf_token") != session['csrf_token']:
            flash("csrf تایید نشد.", "danger")
            return redirect(url_for("users.start_exam"))

        questions_id = map(lambda q: str(q.id), RealQuestion.query.where(RealQuestion.azmoon_id == exam.id).all())
        for q_id in questions_id:
            user_id = user.id
            selected = request.form.get(q_id)

            if selected == "no_answer":
                continue

            option_id = RealOption.query.filter_by(id=selected).first().id
            a = Answer(for_student=user_id,
                       for_question=q_id,
                       answer=option_id)

            db.session.add(a)
            db.session.commit()
        user.answered = True
        db.session.commit()

        calculate_result(user)
        return render_template("users/azmoon/finished.html", azmoon_name=exam.name)

    session['csrf_token'] = secrets.token_urlsafe(30)

    return render_template("users/azmoon/start_exam.html",
                           csrf_token=session['csrf_token'],
                           Q=RealQuestion,
                           azmoon=exam,
                           A=RealOption,
                           len_=len,
                           zip=zip)


@blueprint.route("/results")
def results():
    user = get_user(session.get("username"))

    if not user:
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    results_for_user = map(lambda result: result.for_azmoon_name,
                           Result.query.filter_by(for_student=user.id).all())

    return render_template("users/azmoon/results.html",
                           results=results_for_user)


@blueprint.route('/results/<name>/')
def result_for(name):
    user = get_user(session.get("username"))

    if not user:
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    result = Result.query.filter_by(for_student=user.id,
                                    for_azmoon_name=name).first()
    
    if not result:
        abort(404)

    
    # z_score
    scores = [s for s in map(lambda result: result.percent,
                             Result.query.filter_by(for_azmoon_name=name).all())]
    
    avg = sum(scores) / len(scores)

    std = calc_S(scores)
    if std == 0:
        std_sample_text = "اندکی منتظر بمانید تا باقی دانش اموزان نیز ازمون را تمام کنند."
    
    else:
        z_score = (result.percent - avg) / std
        std_sample_text = f"تراز سنجش: {round(z_score * 2000 + 5000)}{os.linesep}تراز قلمچی: {round(z_score * 1000 + 5000)}"
    return render_template("users/azmoon/result_for.html",
                           result=result,
                           name=user.username,
                           std_sample_text=std_sample_text)
