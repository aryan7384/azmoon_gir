from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, Length
from apps.users.models import User, Azmoon, RealQuestion
import os


__all__ = ["RegisterAzmoonForm",
           "RegisterUserForm",
           "SubmitOptionForm",
           "SubmitQuestionForm",
           "LoginForm"]


class LoginForm(FlaskForm):
    password = PasswordField("رمز عبور", validators=[DataRequired()])


class RegisterUserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('نام کاربری تکراری است.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError("ایمیل تکراری است.")


class RegisterAzmoonForm(FlaskForm):
    name = StringField('نام آزمون', validators=[DataRequired()])
    users = TextAreaField('کاربران', validators=[DataRequired()])


    def validate_name(self, name):
        if Azmoon.query.filter_by(name=name.data).first():
            raise ValidationError("اسم آزمون تکراری است.")

    def validate_users(self, field):
        users = field.data.strip().split(os.linesep)
        print(users)
        for user in users:
            if not User.query.where(User.username == user).first():
                raise ValidationError(f'نام کاربری {user} یافت نشد.')


class SubmitQuestionForm(FlaskForm):
    text = StringField('متن', validators=[DataRequired(), Length(5, 400)])
    azmoon_name = StringField('نام آزمون', validators=[DataRequired()])

    def validate_azmoon_name(self, field):
        if not Azmoon.query.filter_by(name=field.data).first():
            raise ValidationError("آزمون یافت نشد.")


class SubmitOptionForm(FlaskForm):
    text = StringField('متن', validators=[DataRequired(), Length(5, 100)])
    question_id = IntegerField('آی دی سوال', validators=[DataRequired()])
    is_correct = BooleanField('آيا جواب درست است؟')

    def validate_question_id(self, field):
        q_id = field.data
        if not RealQuestion.query.where(RealQuestion.id == q_id).first():
            raise ValidationError("ای دی سوال اشتباه است یا سوال ثبت نشده است.")
