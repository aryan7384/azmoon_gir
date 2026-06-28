from flask_hashing import Hashing
from flask_mailman import Mail
from celery import Celery
import dotenv
import os
__all__ = ["hashing", "mail"]


dotenv.load_dotenv()
hashing = Hashing()
mail = Mail()

celery = Celery(__name__)
celery.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND")
)