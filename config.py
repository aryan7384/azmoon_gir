import dotenv
import os

dotenv.load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = os.getenv("CSRF_SESSION_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USE_TLS = True if os.getenv("MAIL_USE_TLS") == "True" else False
    MAIL_USE_SSL = True if os.getenv("MAIL_USE_SSL") == "True" else False


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        Config.BASE_DIR,
        'project.db'
    )
