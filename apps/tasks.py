from apps.extensions import celery
from calc_result import grade_desc
from apps.users.models import Result, DescQuestion, DescAnswer
from apps.database import db
from openai import OpenAIError, RateLimitError
import redis

r = redis.Redis(host="localhost", port=6379, db=0,
                decode_responses=True)

@celery.task(
    autoretry_for=(OpenAIError,TimeoutError, RateLimitError),
    retry_kwargs={"max_retries": 10},
    retry_backoff=True,
    retry_jitter=True,
    retry_backoff_max=20
)
def grade_submission(user_id, exam_id, manfi=False):
    questions = DescQuestion.query.filter_by(azmoon_id=exam_id).all()
    answers = {}
    for q in questions:
        a = DescAnswer.query.filter_by(desc_question_id=q.id,
                                       student_id=user_id).first()
        answers[q.id] = a.answer

    try:
        percent = grade_desc(questions, answers, user_id, manfi)
        r.set("openai_rate_limit", "0")
    
    except RateLimitError:
        r.set("openai_rate_limit", "1")
        raise


    new_result = Result(for_student=user_id,
                        for_azmoon_id=questions[0].azmoon_id,
                        percent=percent)
    db.session.add(new_result)
    db.session.commit()
