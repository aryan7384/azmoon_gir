from ..database import BaseModel
from sqlalchemy import String, ForeignKey, Integer
from typing import List
from sqlalchemy.orm import mapped_column, Mapped, relationship

__all__ = ["User",
           "Azmoon",
           "RealQuestion",
           "RealOption",
           "Answer",
           "Result",
           "UserState",
           "Teacher",
           "DescQuestion",
           "DescAnswer"]


class Teacher(BaseModel):
    username: Mapped[str] = mapped_column(String(50),
                                          unique=True,
                                          nullable=False)
    password = mapped_column(String(256), nullable=False)
    student_limit = mapped_column(Integer, nullable=False, default=-1)


class User(BaseModel):
    __tablename__ = 'user'

    username = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(70), unique=False, nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    azmoon_id = mapped_column(
        ForeignKey('azmoon.id'),
        nullable=True,
        default=None
    )

    answered: Mapped[bool] = mapped_column(nullable=True, default=None)

    azmoon: Mapped["Azmoon"] = relationship(
        "Azmoon",
        back_populates="users"
    )

    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    results: Mapped[List["Result"]] = relationship(
        "Result",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    user_state: Mapped[List["UserState"]] = relationship(
        "UserState",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.username})"


class Azmoon(BaseModel):
    __tablename__ = 'azmoon'

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_available: Mapped[bool] = mapped_column(nullable=False, default=False)
    exam_type: Mapped[int] = mapped_column(nullable=True, default=0)
    questions: Mapped[List["RealQuestion"]] = relationship(
        "RealQuestion",
        back_populates="azmoon",
        cascade="all, delete-orphan"
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="azmoon"
    )

    results: Mapped[List["Result"]] = relationship(
        "Result",
        back_populates="azmoon",
        cascade="all, delete-orphan"
    )

    users_state: Mapped[List["UserState"]] = relationship(
        "UserState",
        back_populates="azmoon",
        cascade="all, delete-orphan"
    )

class RealQuestion(BaseModel):
    __tablename__ = 'real_question'

    title = mapped_column(String(400))

    question_type: Mapped[int] = mapped_column(nullable=True, default=0)
    answer: Mapped[str] = mapped_column(String(400), nullable=True)
    azmoon_id: Mapped[int] = mapped_column(
        ForeignKey('azmoon.id', name='fk_real_question_azmoon_id'),
        nullable=False
    )

    azmoon: Mapped["Azmoon"] = relationship(
        "Azmoon",
        back_populates="questions"
    )

    options: Mapped[List["RealOption"]] = relationship(
        "RealOption",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan"
    )


class RealOption(BaseModel):
    __tablename__ = 'real_option'

    text = mapped_column(String(100), nullable=False)
    is_correct: Mapped[bool] = mapped_column(default=False, nullable=False)


    question_id: Mapped[int] = mapped_column(
        ForeignKey('real_question.id', name="fk_real_option_question_id"),
        nullable=False
    )

    question: Mapped["RealQuestion"] = relationship(
        "RealQuestion",
        back_populates="options"
    )

    answers: Mapped[List["Answer"]] = relationship(
        "Answer",
        back_populates="option",
        cascade="all, delete-orphan"
    )

class DescQuestion(BaseModel):
    __tablename__ = "desc_question"
    azmoon_id: Mapped[int]
    text = mapped_column(String(400), nullable=False)
    desc_answer = mapped_column(String(2000), nullable=False)
    photo_name = mapped_column(String(100), nullable=True)


class DescAnswer(BaseModel):
    __tablename__ = "desc_answer"
    azmoon_id: Mapped[int] = mapped_column(nullable=False)
    student_id: Mapped[int] = mapped_column(nullable=False)
    desc_question_id: Mapped[int] = mapped_column(nullable=False)
    answer: Mapped[str] = mapped_column(String(500), nullable=False)
    is_true: Mapped[int] = mapped_column(nullable=True)


class Answer(BaseModel):
    __tablename__ = 'answer'

    for_student: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        nullable=False
    )

    for_question: Mapped[int] = mapped_column(
        ForeignKey('real_question.id'),
        nullable=False
    )

    answer: Mapped[int] = mapped_column(
        ForeignKey('real_option.id'),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="answers"
    )

    question: Mapped["RealQuestion"] = relationship(
        "RealQuestion",
        back_populates="answers"
    )

    option: Mapped["RealOption"] = relationship(
        "RealOption",
        back_populates="answers"
    )


class Result(BaseModel):
    __tablename__ = 'result'

    for_student: Mapped[int] = mapped_column(
        ForeignKey('user.id'),
        nullable=False
    )

    for_azmoon_id: Mapped[str] = mapped_column(
        ForeignKey('azmoon.id'),
        nullable=False
    )

    percent: Mapped[float] = mapped_column(nullable=False, default=0)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="results"
    )

    azmoon: Mapped["Azmoon"] = relationship(
        "Azmoon",
        back_populates="results"
    )


class UserState(BaseModel):
    __tablename__ = 'user_state'  # اضافه شد

    user_id: Mapped[int] = mapped_column('student_id', ForeignKey('user.id', name='fk_real_user_state_id'))
    azmoon_id: Mapped[int] = mapped_column('exam_id', ForeignKey('azmoon.id', name='fk_real_exam_id'))

    state: Mapped[str] = mapped_column(String(300), default="Normal")

    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_state"
    )

    azmoon: Mapped["Azmoon"] = relationship(
        "Azmoon",
        back_populates="users_state"
    )
