from flask_hashing import Hashing
from flask_mailman import Mail
__all__ = ["hashing", "calc_S", "mail"]


def calc_S(scores):
    S = 0
    for i in scores:
        S += (i - sum(scores) / len(scores)) ** 2
    return (S / len(scores)) ** 0.5


hashing = Hashing()
mail = Mail()
