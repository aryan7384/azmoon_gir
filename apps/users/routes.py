from flask import Blueprint, render_template, redirect, url_for, flash, session, request, abort
from .forms import *
from ..database import db
from .models import *
from ..extensions import *
import calc_result
from apps import tasks
import os
import secrets
import dotenv
import random
from flask_mailman import EmailMessage

dotenv.load_dotenv()

blueprint = Blueprint('users', __name__)


def get_email(username):
    user = get_user(username)
    return user.email


def get_user(username):
    return User.query.filter_by(username=username).first()


def calculate_result(user):
    user_azmoon = Azmoon.query.filter_by(id=user.azmoon_id).first()
    user.azmoon_id = None
    user.answered = True
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

    new_result = Result(for_student=user.id,
                        for_azmoon_id=user_azmoon.id,
                        percent=score)

    db.session.add(new_result)
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
        return redirect(url_for('users.login'))

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

    session.pop("username")
    flash("با موفقیت خارج شدید.", "success")
    return redirect(url_for("home.home"))


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
                                          update_password_form.old_password.data, salt=os.getenv("SALT")
                                      )).count()):
            flash("رمز اشتباه است", "danger")
            return render_template("users/update_password.html", form=update_password_form)
        hashed_password = hashing.hash_value(update_password_form.new_password.data,
                                             salt=os.getenv("SALT"))
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
            user.password = hashing.hash_value(password := str(random.randint(10000000, 99999999)),
                                               salt=os.getenv("SALT"))
            body = "<h1>ذهن ران</h1><h2>باز نشانی رمز عبور</h2><p style='direction: rtl'>رمز جدید پنل شما:" \
                   f"{password}</p>"
            msg = EmailMessage(
                subject='بازنشانی رمز عبور',
                body=body,
                to=[email]
            )
            msg.content_subtype = "html"
            msg.send()
            db.session.commit()
            flash("رمز جدید به ایمیل شما ارسال شد. بعد از ورود به حساب کاربری حتما ان را تغییر دهید.",
                  "success")
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

    has_exam = bool(Azmoon.query.where(Azmoon.id == get_user(username).azmoon_id,
                                       Azmoon.is_available == True).first()) and (not get_user(username).answered)
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
        
        if exam.exam_type == 0:
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
            user_state = user.user_state
            user_state.state = "پایان ازمون"
            db.session.commit()
            calculate_result(user)
            return render_template("users/azmoon/finished.html", azmoon_id=exam.id)

        else:
            questions = DescQuestion.query.filter_by(azmoon_id=exam.id).all()
            for q in questions:
                new_answer = DescAnswer(
                    azmoon_id=exam.id,
                    student_id=user.id,
                    desc_question_id=q.id,
                    answer=request.form[str(q.id)]
                )
                db.session.add(new_answer)
                db.session.commit()
            
            tasks.grade_submission.delay(user.id, exam.id, False)
            user.answered = True
            user.azmoon_id = None
            db.session.commit()
            user_state = user.user_state
            user_state.state = "پایان ازمون"
            db.session.commit()
            return render_template("users/azmoon/finish-desc.html")


    user_state = UserState.query.filter_by(user_id=user.id).first()
    user_state.state = "در حال آزمون دادن"
    db.session.commit()
    session['csrf_token'] = secrets.token_urlsafe(30)

    if exam.exam_type == 0:
        return render_template("users/azmoon/start_exam.html",
                               csrf_token=session['csrf_token'],
                               Q=RealQuestion,
                               azmoon=exam,
                               A=RealOption,
                               len_=len,
                               zip=zip)

    else:
        return render_template("users/azmoon/start_exam.html",
                               csrf_token=session["csrf_token"],
                               azmoon=exam,
                               Q=DescQuestion,
                               enum=enumerate)


@blueprint.route("/results")
def results():
    user = get_user(session.get("username"))

    if not user:
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    results_for_user = Result.query.filter_by(for_student=user.id).all()

    return render_template("users/azmoon/results.html",
                           results=results_for_user)


@blueprint.route('/results/<id_>/')
def result_for(id_):
    user = get_user(session.get("username"))

    if not user:
        flash("لطفا دوباره وارد شوید.", "info")
        return redirect(url_for('users.login'))

    all_results = Result.query.filter_by(for_azmoon_id=id_).all()

    user_result = Result.query.filter_by(
        for_student=user.id,
        for_azmoon_id=id_
    ).first()

    if not user_result:
        abort(404)

    # z-score
    scores = [r.percent for r in all_results]

    avg = sum(scores) / len(scores)

    std = calc_result.calc_S(scores)
    if std == 0:
        std = 1

    # rank
    results_for_rank = [
        (r.id, r.percent)
        for r in all_results
    ]

    results_for_rank.sort(key=lambda item: -item[1])

    rank = results_for_rank.index(
        (user_result.id, user_result.percent)
    ) + 1

    z_score = (user_result.percent - avg) / std

    std_sample_text = (
        f"تراز سنجش: {round(z_score * 2000 + 10000)} | "
        f"تراز قلمچی: {round(z_score * 1000 + 5000)}"
    )

    results_for_user = []

    exam = Azmoon.query.filter_by(id=id_).first()

    if exam.exam_type == 0:
        for q in RealQuestion.query.filter_by(azmoon_id=id_).all():
            answer = Answer.query.filter_by(
                for_question=q.id,
                for_student=user.id
            ).first()

            if not answer:
                continue

            option = RealOption.query.filter_by(
                id=answer.answer
            ).first()

            correct_option = RealOption.query.filter_by(
                question_id=q.id,
                is_correct=True
            ).first()

            results_for_user.append({
                "question": q.title,
                "answer": option.text,
                "is_true": "t" if option.id == correct_option.id else "f"
            })

    else:
        for q in DescQuestion.query.filter_by(
            azmoon_id=id_
        ).all():

            answer = DescAnswer.query.filter_by(
                student_id=user.id,
                desc_question_id=q.id
            ).first()

            if not answer:
                continue

            results_for_user.append({
                "question": q.text,
                "answer": answer.answer,
                "is_true": "t" if answer.is_true else "f"
            })

    return render_template(
        "users/azmoon/result_for.html",
        result=user_result,
        name=user.username,
        std_sample_text=std_sample_text,
        rank=rank,
        round=round,
        results_for_user=results_for_user
    )
