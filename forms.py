from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, SelectField,SelectMultipleField,PasswordField, SubmitField
from wtforms.validators import DataRequired ,Length, EqualTo
from datetime import date


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    field = StringField('Field', validators=[DataRequired()])
    mark = IntegerField('Mark', validators=[DataRequired()])
    students = SelectMultipleField('Students', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create')

class SprintForm(FlaskForm):
    sprint_name = StringField('Sprint Name', validators=[DataRequired()])
    sprint_number = IntegerField('Sprint Number', validators=[DataRequired()])
    progress_choices = [('in_progress', 'In Progress'), ('recent', 'Recent'), ('done', 'Done')]
    progress = SelectField('Progress', choices=progress_choices, validators=[DataRequired()])
    review_choices = [('bad', 'Bad'), ('good', 'Good'), ('perfect', 'Perfect')]
    review = SelectField('Review', choices=review_choices, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today(), format='%Y-%m-%d')
    deadline = DateField('Deadline', validators=[DataRequired()], format='%Y-%m-%d')
    project = SelectField('Project', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create')


class UpdateSprintForm(FlaskForm):
    progress_choices = [('in_progress', 'In Progress'), ('recent', 'Recent'), ('done', 'Done')]
    progress = SelectField('Progress', choices=progress_choices, validators=[DataRequired()])
    review_choices = [('bad', 'Bad'), ('good', 'Good'), ('perfect', 'Perfect')]
    review = SelectField('Review', choices=review_choices, validators=[DataRequired()])
    deadline = DateField('Deadline', validators=[DataRequired()], format='%Y-%m-%d')
    submit = SubmitField('Update')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RequestForm(FlaskForm):
    content = SelectField('Content', choices=[('teacher', 'Update To Teacher'), ('admin', 'Update To Admin')], validators=[DataRequired()])

class UpdateStudentForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=50)])
    student_id = StringField('Student ID', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Update')

class UpdateTeacherForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=50)])
    teacher_id = StringField('Teacher ID', validators=[DataRequired(), Length(max=20)])
    study_field = StringField('Study Field', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Update')

class UpdateAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=50)])
    admin_id = StringField('Admin ID', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Update')
