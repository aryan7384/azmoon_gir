from flask_hashing import Hashing
import math
# from kavenegar import KavenegarAPI
# import os, dotenv
# dotenv.load_dotenv()
__all__ = ["hashing", "calc_S"]


def calc_S(scores):
    S = 0
    for i in scores:
        S += (i - sum(scores) / len(scores)) ** 2
    return (S / len(scores)) ** 0.5


hashing = Hashing()
# sms_api = KavenegarAPI(os.getenv("KAVENEGAR"))