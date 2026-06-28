from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from apps.users.models import Teacher


__all__ = ["LoginForm",
           "RegisterTeacherForm"]


class LoginForm(FlaskForm):
    password = PasswordField("رمز عبور", validators=[DataRequired()])


class RegisterTeacherForm(FlaskForm):
    username = StringField("نام کاربری", validators=[DataRequired()])
    password = StringField("رمز عبور", validators=[DataRequired()])
    limit = IntegerField("محدودیت دانش اموزان", validators=[DataRequired()])

    def validate_username(self, field):
        if Teacher.query.filter_by(username=field.data).first():
            raise ValidationError("نام کاربری تکراری است.")
        
    def validate_limit(self, field):
        if -1 > field.data:
            raise ValidationError("خطا در ورودی.")
