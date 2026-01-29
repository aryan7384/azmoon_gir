from flask import Flask
from apps.users.routes import blueprint as users_blueprint
from apps.admin.routes import blueprint as admin_blueprint
from apps.home.routes import blueprint as home_blueprint
from apps.teachers.routes import blueprint as teachers_blueprint
from apps.database import db
from apps.users.models import *
from apps.extensions import hashing
from datetime import timedelta
import apps.exceptions as app_exp
from flask_migrate import Migrate
import random
import os
import dotenv


def register_blueprints(application: Flask):
    application.register_blueprint(users_blueprint)
    application.register_blueprint(admin_blueprint)
    application.register_blueprint(home_blueprint)
    application.register_blueprint(teachers_blueprint)


def register_error_handlers(application: Flask):
    application.register_error_handler(404, app_exp.page_not_found)
    application.register_error_handler(500, app_exp.server_error)


def register_shell_context(application: Flask):
    def context():
        return {
            "App": application,
            "db": db,
            "User": User,
            "Azmoon": Azmoon,
            "RealOption": RealOption,
            "RealQuestion": RealQuestion,
            "Answer": Answer,
            "admin_blueprint": admin_blueprint,
            "home_blueprint": home_blueprint,
            "users_blueprint": users_blueprint,
            "hashing": hashing
        }

    application.shell_context_processor(
        context
    )


dotenv.load_dotenv()

app = Flask(__name__)
app.config.from_object(os.getenv("DEV_DEP"))

app.permanent_session_lifetime = timedelta(days=float(os.getenv("SESSION_LIFETIME_DAYS")),
                                           hours=float(os.getenv("SESSION_LIFETIME_HOURS")),
                                           minutes=float(os.getenv("SESSION_LIFETIME_MINUTES")))

register_blueprints(app)
register_error_handlers(app)
register_shell_context(app)

db.init_app(app)

migrate = Migrate(app, db)

hashing.init_app(app)


@app.template_filter('shuffle')
def shuffle_filter(iterable):
    items = iterable
    random.shuffle(items)
    return items
