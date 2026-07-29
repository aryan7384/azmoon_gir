from flask import Blueprint, render_template

blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def home():
    return render_template("home/index.html")

@blueprint.route("/student_guide")
def student_guide():
    return render_template("home/student_guide.html")

@blueprint.route("/teacher_guide")
def teacher_guide():
    return render_template("home/teacher_guide.html")
