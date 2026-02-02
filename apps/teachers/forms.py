from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from apps.database import db
from apps.users.models import *
import os


class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    submit = SubmitField('ورود')


class RegisterUserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(max=50)])
    name = StringField("نام و نام خانوادگی", validators=[DataRequired()])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    submit = SubmitField("ثبت نام")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("نام کاربری تکراری است.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("ایمیل تکراری است.")


class RegisterExamForm(FlaskForm):
    azmoon_name = StringField('نام آزمون', validators=[DataRequired(),
                                                       Length(max=50)])
    users = TextAreaField('کاربرانی که ازمون برای انها فعال میشود')

    def validate_azmoon_name(self, field):
        if Azmoon.query.filter_by(name=field.data).first():
            raise ValidationError("نام آزمون تکراری است")

    def validate_users(self, field):
        users = field.data.strip().split(os.linesep)
        if len(users) == 1 and users[0] == "":
            return
        for user in users:
            if not User.query.filter_by(username=user).first():
                raise ValidationError(f"نام کاربری {user} یافت نشد.")


class ModifyExamForm(FlaskForm):
    azmoon_name = StringField('نام آزمون', validators=[DataRequired(),
                                                       Length(max=50)])

    users = TextAreaField('کاربرانی که ازمون برای انها فعال میشود')

    def validate_users(self, field):
        users = field.data.strip().split(os.linesep)
        if len(users) == 1 and users[0] == "":
            pass
        else:
            for user in users:
                if not User.query.filter_by(username=user).first():
                    raise ValidationError(f"نام کاربری {user} یافت نشد.")
