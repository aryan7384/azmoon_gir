import secrets
from flask import Blueprint, render_template, redirect, url_for, session, flash, request, render_template_string
from .forms import *
from ..database import db
from apps.users.models import *
from ..extensions import *
import os
import dotenv
from flask_mailman import EmailMessage

dotenv.load_dotenv()

blueprint = Blueprint('teachers', __name__)


def check_teacher_logged_in():
    if not session.get('teacher_username'):
        flash("اول وارد شوید.", "info")
        return redirect(url_for('teachers.login'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if not teacher:
        flash("لطفا مجدد وارد شوید", "info")
        del session['teacher_username']
        return redirect(url_for('teachers.login'))

    return None


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
    if result := check_teacher_logged_in():
        return result
    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    exams = Azmoon.query.filter_by(teacher_id=teacher.id).all()
    users = User.query.filter_by(teacher_id=teacher.id).all()

    session['csrf_token'] = secrets.token_urlsafe(32)
    answers = []
    answers_list = Answer.query.all()
    for i in answers_list:
        user = User.query.filter_by(id=i.for_student).first()
        if user.teacher_id != teacher.id:
            continue

        question = RealQuestion.query.filter_by(id=i.for_question).first()
        exam_name = Azmoon.query.filter_by(id=question.azmoon_id).first().name
        new_answer = {"stdname": user.name,
                      "question": question.title,
                      "exam_name": exam_name,
                      "answer": RealOption.query.filter_by(id=i.answer).first().text,
                      "is_correct":
                          "t" if RealOption.query.filter_by(id=i.answer).first().is_correct else "f"}
        answers.append(new_answer)

    all_results = Result.query.all()
    results = []

    for i in all_results:
        user = User.query.filter_by(id=i.for_student).first()
        if user.teacher_id != teacher.id:
            continue

        results.append({"stdname": user.name,
                        "examname": i.azmoon.name,
                        "percent": i.percent})

    states = []
    for i in exams:
        exam_states = i.users_state
        exam_states_dict = []
        for j in exam_states:
            exam_states_dict.append(
                {"exam_name": i.name,
                 "student_name": j.user.name,
                 "current": j.state}
            )
        states.extend(exam_states_dict)

    return render_template("teachers/teacher-panel.html",
                           exams=exams,
                           users=users,
                           csrf_token=session['csrf_token'],
                           answers=answers,
                           results=results,
                           states=states)


@blueprint.route("/teacher/update-password", methods=['GET', 'POST'])
def update_password():
    if result := check_teacher_logged_in():
        return result

    form = UpdatePasswordForm()
    if form.validate_on_submit():
        teacher = Teacher.query.filter_by(username=session["teacher_username"]).first()
        if hashing.hash_value(form.old_password.data,
                              salt=os.getenv("SALT")) != teacher.password:
            flash("رمز عبور وارد شده درست نیست.", "danger")
            return redirect(url_for('teachers.update_password'))

        teacher.password = hashing.hash_value(form.new_password.data,
                                              salt=os.getenv("SALT"))
        db.session.commit()
        flash("رمز عبور با موفقیت تغییر یافت.")
        return redirect(url_for('teachers.dashboard'))

    return render_template("teachers/update-password.html",
                           form=form)


@blueprint.route("/teacher/azmoon/register", methods=['GET', 'POST'])
def register_azmoon():
    if result := check_teacher_logged_in():
        return result

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    form = RegisterExamForm()
    if form.validate_on_submit():
        users = form.users.data.strip().splitlines()
        for i in users:
            user = User.query.filter_by(teacher_id=teacher.id,
                                        username=i).first()
            if not user:
                flash(f"کاربر {i} برای معلم دیگری ثبت شده.")
                return redirect(url_for('teachers.register_azmoon'))
        azmoon = Azmoon(teacher_id=teacher.id,
                        name=form.azmoon_name.data,
                        is_available=False)
        db.session.add(azmoon)
        db.session.commit()
        if len(users) != 0:
            for user in users:
                new_user = User.query.filter_by(username=user).first()
                if not new_user.azmoon_id and not new_user.answered:
                    flash(f"دانش آموز {new_user.name}یک آزمون فعال دارد.")
                    return redirect(url_for('teachers.register_azmoon'))
                new_user.azmoon_id = azmoon.id
                state = UserState(user_id=new_user.id,
                                  azmoon_id=azmoon.id,
                                  state="معمولی")
                db.session.add(state)
                db.session.commit()

        flash("آزمون جدید ثبت شد.")
        return redirect(url_for("teachers.dashboard"))

    return render_template("teachers/register-exam.html",
                           form=form)


@blueprint.route("/teacher/azmoon/delete/<id>", methods=['POST'])
def delete_azmoon(id):
    if result := check_teacher_logged_in():
        return result

    if session.get('csrf_token') != request.form['csrf_token']:
        flash("CSRF تایید نشد.")
        return redirect(url_for('teachers.dashboard'))

    azmoon = Azmoon.query.filter_by(id=id).first()
    if not azmoon:
        flash("آزمون یافت نشد")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if azmoon.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید.")
        return redirect(url_for('teachers.dashboard'))

    users = User.query.filter_by(azmoon_id=azmoon.id).all()
    for i in users:
        i.azmoon_id = 0
        i.answered = True
    db.session.commit()

    db.session.delete(azmoon)
    db.session.commit()
    flash(f"آزمون {azmoon.name}با موفقیت حذف شد. ")
    return redirect(url_for('teachers.dashboard'))


@blueprint.route("/teacher/azmoon/modify/<id>", methods=['GET', 'POST'])
def modify_azmoon(id):
    if result := check_teacher_logged_in():
        return result

    exam = Azmoon.query.where(Azmoon.id == id).first()
    if not exam:
        flash("آزمون یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if exam.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید")
        return redirect(url_for('teachers.dashboard'))

    form = ModifyExamForm()
    if form.validate_on_submit():
        if exam.is_available:
            flash("امکان تغییر اطلاعات آزمون پس از ثبت نهایی ان وجود ندارد.")
            return redirect(url_for("teachers.dashboard"))

        all_exams = Azmoon.query.where(Azmoon.name != exam.name,
                                       Azmoon.teacher_id == teacher.id).all()
        names = []
        for e in all_exams:
            names.append(e.name)

        if form.azmoon_name.data in names:
            flash("نام آزمون تکراری است.")
            return redirect(url_for('teachers.modify_azmoon', id=id))

        exam.name = form.azmoon_name.data
        exam.is_available = form.is_available.data
        db.session.commit()

        students = exam.users
        for i in students:
            i.azmoon_id = 0
            i.answered = True
            db.session.delete(UserState.query.filter_by(azmoon_id=exam.id).first())
        db.session.commit()
        users = form.users.data.strip().splitlines()
        for user in users:
            user_record = User.query.filter_by(username=user).first()
            if user_record.teacher_id != teacher.id:
                flash(f"کاربر {user_record.username}برای شما ثبت نشده است.")
                return redirect(url_for('teachers.modify_azmoon', id=id))
            state = UserState(user_id=user_record.id,
                              azmoon_id=exam.id,
                              state="normal")
            db.session.add(state)
            db.session.commit()
            if form.is_available.data:
                user_record = User.query.filter_by(username=user).first()
                user_record.answered = False
                user_record.azmoon_id = exam.id
                state = UserState.query.filter_by(user_id=user_record.id,
                                                  azmoon_id=user_record.azmoon_id).first()
                state_text = """
                هنوز ازمون نداده است.
                <form method='POST' action={{url_for('teachers.send_mail', user_id=user_id)}}>
                <input type='submit' value='ارسال ایمیل'>
                </form>"""
                state.state = render_template_string(state_text,
                                                     user_id=user_record.id)

            db.session.commit()

        flash("ازمون با موفقیت به روزرسانی شد.")
        return redirect(url_for('teachers.dashboard'))

    form.azmoon_name.data = exam.name
    users_records = User.query.filter_by(azmoon_id=exam.id).all()
    users = []
    for i in users_records:
        users.append(i.username)
    form.users.data = os.linesep.join(users)
    if exam.is_available:
        flash("امکان تغییر اطلاعات آزمون پس از ثبت نهایی ان وجود ندارد.")
        return redirect(url_for("teachers.dashboard"))
    return render_template("teachers/modify_exam.html",
                           form=form)


@blueprint.route("/teacher/users/register", methods=['GET', 'POST'])
def register_user():
    if result := check_teacher_logged_in():
        return result

    form = RegisterUserForm()
    if form.validate_on_submit():
        teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
        new_user = User(username=form.username.data,
                        name=form.name.data,
                        email=form.email.data,
                        teacher_id=teacher.id,
                        password=hashing.hash_value("#" + form.username.data + "123",
                                                    salt=os.getenv("SALT")),
                        answered=True,
                        azmoon_id=0)

        db.session.add(new_user)
        db.session.commit()
        flash("کاربر ثبت شد.")
        return redirect(url_for('teachers.dashboard'))

    return render_template('teachers/register-user.html', form=form)


@blueprint.route("/teacher/users/delete/<id>", methods=['POST'])
def delete_user(id):
    if result := check_teacher_logged_in():
        return result

    if session.get('csrf_token') != request.form['csrf_token']:
        flash("CSRF تایید نشد.")
        return redirect(url_for('teachers.dashboard'))

    user = User.query.filter_by(id=id).first()
    if not user:
        flash("کاربر یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if user.teacher_id != teacher.id:
        flash("شما اجازه ی دسترسی به کاربر مد نظر را ندارید.")
        return redirect(url_for('teachers.dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash(f"کاربر {user.name} با موفقیت حذف شد.")
    return redirect(url_for('teachers.dashboard'))


@blueprint.route('/teacher/users/modify/<id>', methods=['GET', 'POST'])
def modify_user(id):
    if result := check_teacher_logged_in():
        return result

    user = User.query.filter_by(id=id).first()
    if not user:
        flash("کاربر یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if user.teacher_id != teacher.id:
        flash("شما اجازه ی دسترسی به کاربر مد نظر را ندارید.")
        return redirect(url_for('teachers.dashboard'))

    form = ModifyUserForm()
    if form.validate_on_submit():
        # check form datas
        if User.query.where(User.email == form.email.data,
                            User.email != user.email).first():
            flash("ایمیل تکراری است.")
            return redirect(url_for('teachers.modify_user', id=id))

        user.name = form.name.data
        user.email = form.email.data
        db.session.commit()
        flash("تغییرات اعمال شد.")
        return redirect(url_for('teachers.dashboard'))

    form.email.data = user.email
    form.name.data = user.name
    return render_template('teachers/modify-user.html',
                           form=form)


@blueprint.route('/teacher/questions/<id>', methods=['GET'])
def questions(id):
    if result := check_teacher_logged_in():
        return result

    exam = Azmoon.query.filter_by(id=id).first()
    if not exam:
        flash("آزمون یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if exam.teacher_id != teacher.id:
        flash("شما دسترسی به آزمون ندارید.")
        return redirect(url_for('teachers.dashboard'))

    questions = RealQuestion.query.filter_by(azmoon_id=id).all()
    choices = {}
    for i in questions:
        choices[i.id] = RealOption.query.filter_by(question_id=i.id).all()

    session['csrf_token'] = secrets.token_urlsafe(32)
    return render_template("teachers/questions.html",
                           questions=questions,
                           exam=exam,
                           choices=choices,
                           csrf_token=session['csrf_token'])


@blueprint.route('/teacher/questions/add/<exam_id>', methods=['GET', 'POST'])
def add_question(exam_id):
    if result := check_teacher_logged_in():
        return result

    exam = Azmoon.query.filter_by(id=exam_id).first()
    if not exam:
        flash("آزمون یافت نشد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if exam.teacher_id != teacher.id:
        flash("شما دسترسی به آزمون ندارید.")
        return redirect(url_for('teachers.dashboard'))

    if exam.is_available:
        flash("امکان افزودن سوال پس از ثبت شدن آزمون، وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    form = AddQuestionForm()
    if form.validate_on_submit():
        if RealQuestion.query.filter_by(title=form.title.data,
                                        azmoon_id=exam.id).first():
            flash("عنوان تکراری است.")
            return redirect(url_for('teachers.add_question', id=exam_id))
        new_question = RealQuestion(title=form.title.data,
                                    azmoon_id=exam.id)
        db.session.add(new_question)
        db.session.commit()
        flash("سوال ثبت شد.")
        return redirect(url_for('teachers.questions', id=exam_id))
    return render_template("teachers/add-question.html",
                           form=form,
                           exam=exam)


@blueprint.route('/teacher/questions/delete/<exam_id>/<q_id>', methods=['POST'])
def delete_question(exam_id, q_id):
    if result := check_teacher_logged_in():
        return result

    if session.get('csrf_token') != request.form['csrf_token']:
        flash("CSRF تایید نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    question = RealQuestion.query.filter_by(id=q_id).first()

    if not question:
        flash("سوال یافت نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    if not Azmoon.query.filter_by(id=exam_id).first():
        flash("آزمون وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if Azmoon.query.filter_by(id=exam_id).first().teacher_id != teacher.id or \
            Azmoon.query.filter_by(id=exam_id).first().id != question.azmoon_id:
        flash('شما دسترسی به این ازمون را ندارید یا ایدی سوال برای این ازمون نیست.')
        return redirect(url_for('teachers.questions', id=exam_id))

    if Azmoon.query.filter_by(id=exam_id).first().is_available:
        flash("امکان حذف سوال پس از ثبت شدن آزمون، وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    db.session.delete(question)
    db.session.commit()
    flash("سوال حذف شد.")
    return redirect(url_for('teachers.questions', id=exam_id))


@blueprint.route("/teacher/questions/modify/<exam_id>/<q_id>", methods=['GET', 'POST'])
def modify_question(exam_id, q_id):
    if result := check_teacher_logged_in():
        return result

    question = RealQuestion.query.filter_by(id=q_id).first()

    if not question:
        flash("سوال یافت نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    if not Azmoon.query.filter_by(id=exam_id).first():
        flash("آزمون وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if Azmoon.query.filter_by(id=exam_id).first().teacher_id != teacher.id or \
            Azmoon.query.filter_by(id=exam_id).first().id != question.azmoon_id:
        flash('شما دسترسی به این ازمون را ندارید یا ایدی سوال برای این ازمون نیست.')
        return redirect(url_for('teachers.questions', id=exam_id))

    if Azmoon.query.filter_by(id=exam_id).first().is_available:
        flash("امکان تغییر سوال پس از ثبت شدن آزمون، وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    form = ModifyQuestionForm()
    if form.validate_on_submit():
        question.title = form.title.data
        db.session.commit()
        flash("سوال با موفقیت تغییر یافت.", category="success")
        return redirect(url_for('teachers.questions', id=exam_id))

    form.title.data = question.title
    choices = RealOption.query.filter_by(question_id=q_id).all()
    return render_template("teachers/modify-question.html", form=form,
                           exam_id=exam_id,
                           q_id=q_id,
                           choices=choices)


@blueprint.route("/teacher/questions/add-choice/<exam_id>/<q_id>", methods=['GET', 'POST'])
def add_choice(exam_id, q_id):
    if result := check_teacher_logged_in():
        return result

    question = RealQuestion.query.filter_by(id=q_id).first()

    if not question:
        flash("سوال یافت نشد.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    if not Azmoon.query.filter_by(id=exam_id).first():
        flash("آزمون وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if Azmoon.query.filter_by(id=exam_id).first().teacher_id != teacher.id or str(question.azmoon_id) != exam_id:
        flash("شما دسترسی به این آزمون یا سوال را ندارید.")
        return redirect(url_for('teachers.questions', id=exam_id))

    if Azmoon.query.filter_by(id=exam_id).first().is_available:
        flash("امکان افزودن گزینه پس از ثبت شدن آزمون، وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    form = AddChoiceForm()
    if form.validate_on_submit():
        if RealOption.query.filter_by(question_id=q_id,
                                      text=form.text.data).first():
            flash("متن گزینه تکراری است.", category="error")
            return redirect(url_for('teachers.add_choice', exam_id=exam_id, q_id=q_id))

        if form.is_correct.data and RealOption.query.filter_by(question_id=q_id,
                                                               is_correct=True).first():
            flash("نمیتوانید سوالی با ۲ گزینه صحیح داشته باشید.", category="error")
            return redirect(url_for('teachers.add_choice',
                                    exam_id=exam_id,
                                    q_id=q_id))

        choice = RealOption(question_id=q_id,
                            text=form.text.data,
                            is_correct=form.is_correct.data)
        db.session.add(choice)
        db.session.commit()
        flash("گزینه اضافه شد.", category="success")
        return redirect(url_for('teachers.questions', id=exam_id))

    return render_template("teachers/add-choice.html",
                           form=form)


@blueprint.route("/teacher/questions/delete-option/<exam_id>/<q_id>/<option_id>", methods=['POST'])
def delete_option(exam_id, q_id, option_id):
    if result := check_teacher_logged_in():
        return result

    if session.get('csrf_token') != request.form['csrf_token']:
        flash("CSRF تایید نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    exam = Azmoon.query.filter_by(id=exam_id).first()
    if not exam:
        flash("آزمون یافت نشد.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if exam.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    question = RealQuestion.query.filter_by(id=q_id).first()
    if not question:
        flash("سوال یافت نشد.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    if str(question.azmoon_id) != exam_id:
        flash("سوال برای شما نیست یا ای دی ازمون با سوال مطابقت ندارد.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    choice = RealOption.query.filter_by(id=option_id).first()
    if not choice:
        flash("ایدی گزینه یافت نشد.", category="error")
        return redirect(url_for('teachers.questions', id=exam_id))

    if str(choice.question_id) != q_id:
        flash("آی دی گزینه برای شما نیست یا سوال با گزینه مطابقت ندارد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    if Azmoon.query.filter_by(id=exam_id).first().is_available:
        flash("امکان حذف گزینه پس از ثبت شدن آزمون، وجود ندارد.")
        return redirect(url_for('teachers.dashboard'))

    db.session.delete(choice)
    db.session.commit()
    flash("گزینه با موفقیت حذف شد.", category="success")
    return redirect(url_for('teachers.questions', id=exam_id))


@blueprint.route("/teacher/send_mail/<user_id>", methods=["POST"])
def send_mail(user_id):
    user = User.query.filter_by(id=user_id).first()
    email = user.email
    body = f"""
<div dir="rtl">
<h1>پیام از طرف معلم</h1>
<p>معلم به شما درخواست شرکت در ازمون داده است.<p>
<a href="{os.getenv("DOMAIN")}{url_for('users.azmoon')}">ورود به آزمون</a>
</div>"""
    msg = EmailMessage(
        subject='پیام از طرف معلم، ذهن زان',
        body=body,
        to=[email]
    )
    msg.content_subtype = "html"
    msg.send()
    flash("پیغام ارسال شد.", category="success")
    return redirect(url_for("teachers.dashboard"))
