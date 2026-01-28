import dotenv
import os

dotenv.load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    CSRF_ENABLED = True
    CSRF_SESSION_KEY = os.getenv("CSRF_SESSION_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        Config.BASE_DIR,
        'project.db'
    )
