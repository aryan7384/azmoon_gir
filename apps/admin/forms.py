from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, TextAreaField, PasswordField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired, ValidationError, Length
from apps.users.models import Teacher
import os


__all__ = ["LoginForm",
           "RegisterTeacherForm",
           "ModifyTeacherForm"]


class LoginForm(FlaskForm):
    password = PasswordField("رمز عبور", validators=[DataRequired()])


class RegisterTeacherForm(FlaskForm):
    username = StringField("نام کاربری", validators=[DataRequired()])
    password = StringField("رمز عبور", validators=[DataRequired()])

    def validate_username(self, field):
        if Teacher.query.filter_by(username=field.data).first():
            raise ValidationError("نام کاربری تکراری است.")
        

class ModifyTeacherForm(FlaskForm):
    username = StringField("نام کاربری", validators=[DataRequired()])
    password = StringField("رمز عبور", validators=[DataRequired()])

    def validate_username(self, field):
        if Teacher.query.filter_by(username=field.data).first():
            raise ValidationError("نام کاربری تکراری است.")
        