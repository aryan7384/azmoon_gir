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
           "Teacher"]


class Teacher(BaseModel):
    username: Mapped[str] = mapped_column(unique=True,
                                          nullable=False)
    password = mapped_column(String(256), nullable=False)


class User(BaseModel):
    __tablename__ = 'user'

    username = mapped_column(String(50), unique=True, nullable=False)
    email = mapped_column(String(80), unique=True, nullable=False)
    password = mapped_column(String(256), nullable=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    azmoon_id = mapped_column(
        Integer,
        ForeignKey('azmoon.id'),
        nullable=True
    )

    answered: Mapped[bool] = mapped_column(nullable=False, default=False)

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

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.username})"


class Azmoon(BaseModel):
    __tablename__ = 'azmoon'

    teacher_id: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_available: Mapped[bool] = mapped_column(nullable=False, default=False)
    questions: Mapped[List["RealQuestion"]] = relationship(
        "RealQuestion",
        back_populates="azmoon",
        cascade="all, delete-orphan"
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="azmoon"
    )


class RealQuestion(BaseModel):
    __tablename__ = 'real_question'

    title = mapped_column(String(400))

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
        back_populates="option"
    )


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

    for_azmoon_name: Mapped[str] = mapped_column(
        ForeignKey('azmoon.name'),
        nullable=False
    )

    percent: Mapped[float] = mapped_column(nullable=False, default=0)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="results"
    )

    azmoon: Mapped["Azmoon"] = relationship(
        "Azmoon"
    )
