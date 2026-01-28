from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, Email, ValidationError
from apps.database import db
from .models import User


__all__ = ['RegisterForm',
           'LoginForm',
           'UpdateProfileForm',
           'UpdatePasswordForm',
           'AnswerForm',
           'PasswordResetForm',]


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(),
                                                   Length(min=5, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])

    def validate_email(self, field):
        user = db.session.execute(db.select(User).where(User.email == field.data)).scalar()
        if user:
            raise ValidationError("Email already exists")

    def validate_username(self, field):
        user = db.session.execute(db.select(User).where(User.username == field.data)).scalar()
        if user:
            raise ValidationError(f"username {field.data} already exists")


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember')


class UpdateProfileForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])


class UpdatePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])


class AnswerForm(FlaskForm):
    answer = StringField('Answer', validators=[DataRequired()])
    submit = SubmitField('Submit')


class PasswordResetForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])

    def validate_username(self, field):
        user = db.session.execute(db.select(User).where(User.username == field.data)).scalar()
        if not user:
            raise ValidationError("Username does not exist")

    def validate_email(self, field):
        email = db.session.execute(db.select(User).where(User.email == field.data)).scalar()
        if not email:
            raise ValidationError("Email does not exist")
