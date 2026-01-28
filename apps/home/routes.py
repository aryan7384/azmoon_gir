from flask import Blueprint, render_template

blueprint = Blueprint('home', __name__)


@blueprint.route('/')
def home():
    return render_template("home/index.html")
