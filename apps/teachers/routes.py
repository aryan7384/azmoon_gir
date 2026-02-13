from flask import Blueprint, render_template, redirect, url_for, session, flash
from .forms import *
from ..database import db
from apps.users.models import *
from ..extensions import *
import os
import dotenv

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
    return render_template("teachers/teacher-panel.html",
                           exams=exams,
                           users=users)


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
        print(users)
        if len(users) != 0:
            for user in users:
                new_user = User.query.filter_by(username=user).first()
                new_user.azmoon_id = azmoon.id
                db.session.commit()

        flash("آزمون جدید ثبت شد.")
        return redirect(url_for("teachers.dashboard"))

    return render_template("teachers/register-exam.html",
                           form=form)


@blueprint.route("/teacher/azmoon/delete/<id>", methods=['POST'])
def delete_azmoon(id):
    if result := check_teacher_logged_in():
        return result

    azmoon = Azmoon.query.filter_by(id=id).first()
    if not azmoon:
        flash("آزمون یافت نشد")
        return redirect(url_for('teachers.dashboard'))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if azmoon.teacher_id != teacher.id:
        flash("شما دسترسی به این آزمون ندارید.")
        return redirect(url_for('teachers.dashboard'))

    users = User.query.filter_by(azmoon_id = azmoon.id).all()
    for i in users:
        i.azmoon_id = 0

    db.session.commit()

    db.session.delete(azmoon)
    db.session.commit()
    flash(f"آزمون {azmoon.name}با موفقیت حذف شد.")
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

        users = form.users.data.strip().splitlines()
        for user in users:
            user_record = User.query.filter_by(username=user).first()
            if user_record.teacher_id != teacher.id:
                flash(f"کاربر {user_record.username}برای شما ثبت نشده است.")
                return redirect(url_for('teachers.modify_azmoon', id=id))
            user_record.azmoon_id = exam.id
            if form.is_available.data:
                user_record.answered = False
            db.session.add(user_record)
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
                        password=hashing.hash_value("#" + form.username.data + "123"))

        db.session.add(new_user)
        db.session.commit()
        flash("کاربر ثبت شد.")
        return redirect(url_for('teachers.dashboard'))

    return render_template('teachers/register-user.html', form=form)


@blueprint.route("/teacher/users/delete/<id>", methods=['POST'])
def delete_user(id):
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
        if User.query.where(User.username == form.username.data,
                            User.username != user.username).first():
            flash("نام کاربری تکراری است.")
            return redirect(url_for('teachers.modify_user'), id=id)

        if User.query.where(User.email == form.email.data,
                            User.email != user.email).first():
            flash("ایمیل تکراری است.")
            return redirect(url_for('teachers.modify_user', id=id))

        user.name = form.name.data
        user.email = form.email.data
        user.username = form.username.data
        user.password = hashing.hash_value(form.password.data,
                                           salt=os.getenv("SALT"))
        db.session.commit()
        flash("تغییرات اعمال شد.")
        return redirect(url_for('teachers.dashboard'))

    form.username.data = user.username
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

    questions = RealQuestion.query.filter_by(id=id).all()
    return render_template("teachers/questions.html",
                           questions=questions,
                           exam=exam)


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

    form = AddQuestionForm()
    if form.validate_on_submit():
        if RealQuestion.query.filter_by(title=form.title.data,
                                        azmoon_id=exam.id).first():
            flash("عنوان تکراری است.")
            return redirect(url_for('teachers.add_question', id=id))
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

    question = RealQuestion.query.filter_by(id=q_id).first()

    if not question:
        flash("سوال یافت نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if Azmoon.query.filter_by(id=exam_id).first().teacher_id != teacher.id or\
            Azmoon.query.filter_by(id=exam_id).first().id != question.azmoon_id:
        flash('شما دسترسی به این ازمون را ندارید یا ایدی سوال برای این ازمون نیست.')
        return redirect(url_for('teachers.questions', id=exam_id))

    db.session.delete(question)
    db.session.commit()
    flash("سوال حذف شد.")
    return redirect(url_for('teachers.questions', id=exam_id))


@blueprint.route("/teacher/questions/modify/<exam_id>/<q_id>")
def modify_question(exam_id, q_id):
    if result := check_teacher_logged_in():
        return result
    
    question = RealQuestion.query.filter_by(id=q_id).first()

    if not question:
        flash("سوال یافت نشد.")
        return redirect(url_for('teachers.questions', id=exam_id))

    
    teacher = Teacher.query.filter_by(username=session['teacher_username']).first()
    if Azmoon.query.filter_by(id=exam_id).first().teacher_id != teacher.id or\
            Azmoon.query.filter_by(id=exam_id).first().id != question.azmoon_id:
        flash('شما دسترسی به این ازمون را ندارید یا ایدی سوال برای این ازمون نیست.')
        return redirect(url_for('teachers.questions', id=exam_id))

    form = ModifyQuestionForm()
    if form.validate_on_submit():
        question.title = form.title.data
        db.session.commit()
        flash("سوال با موفقیت تغییر یافت.")
        return redirect(url_for('teachers.questions', id=exam_id))

    form.title.data = question.title
    return render_template("teachers/questions.html", form=form)
