from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FileField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import User, UserRole
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    profile_image = FileField("Profile Image", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken. Please choose a different one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is already in use. Please choose a different one.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Login")

class ResumeUploadForm(FlaskForm):
    resume_file = FileField("Upload Resume", validators=[
        DataRequired(),
        FileAllowed(["pdf", "docx"], "Only PDF and DOCX files are allowed!")
    ])
    is_primary = BooleanField("Set as primary resume")
    submit = SubmitField("Upload")

class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired()])
    description = TextAreaField("Job Description", validators=[DataRequired()])
    required_skills = TextAreaField("Required Skills", validators=[DataRequired()])
    status = SelectField("Status", choices=[("open", "Open"), ("closed", "Closed")], validators=[DataRequired()])
    closing_date = DateField("Closing Date", format="%Y-%m-%d", validators=[DataRequired()])
    submit = SubmitField("Submit Job Posting")

class ApplicationForm(FlaskForm):
    resume = SelectField('Select Resume', coerce=int, validators=[DataRequired()])
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired(), Length(min=100, max=2000)])
    submit = SubmitField('Submit Application')

class InterviewForm(FlaskForm):
    interview_date = DateField('Interview Date', format='%Y-%m-%d', validators=[DataRequired()])
    interview_time = StringField('Interview Time (HH:MM)', validators=[DataRequired()])
    meeting_link = StringField('Meeting Link', validators=[DataRequired()])
    additional_notes = TextAreaField('Additional Notes')
    submit = SubmitField('Schedule Interview')

# Add forms for profile editing, job posting etc. later

