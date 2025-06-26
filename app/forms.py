from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FileField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from app.models import User, UserRole
from flask_wtf.file import FileAllowed
from markupsafe import Markup

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    email = StringField("Email", validators=[DataRequired(), Email()], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    first_name = StringField("First Name", validators=[DataRequired()], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    last_name = StringField("Last Name", validators=[DataRequired()], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    profile_image = FileField("Profile Image", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")], 
    render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px;  color: green"
        ,})
    submit = SubmitField(Markup('<i class="bi bi-person-plus me-1"></i> Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken. Please choose a different one.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is already in use. Please choose a different one.")

class ProfileEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)])
    profile_image = FileField("Profile Image", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Changes')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("That username is already taken. Please choose a different one.")

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email is already in use. Please choose a different one.")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()], 
            render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,}
 )
    password = PasswordField("Password", validators=[DataRequired()], 
            render_kw={
            "style": "border: 2px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    remember_me = BooleanField("Remember Me", )
    submit = SubmitField("Sign In")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        
    def validate(self):
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            print("===DEBUG=== Form validation failed")
            return False
            
        if self.email.data:
            print(f"===DEBUG=== Form validation - Email length: {len(self.email.data)}")
        if self.password.data:
            print(f"===DEBUG=== Form validation - Password length: {len(self.password.data)}")
        
        # Ensure password field is not empty
        if not self.password.data or not self.password.data.strip():
            print("===DEBUG=== Empty password submitted")
            self.password.errors = ["Password cannot be empty"]
            return False
            
        return True

class ResumeUploadForm(FlaskForm):
    resume_file = FileField("Upload Resume", validators=[
        DataRequired(),
        FileAllowed(["pdf", "docx"], "Only PDF and DOCX files are allowed!")
    ])
    is_primary = BooleanField("Set as primary resume")
    submit = SubmitField(Markup('<i class="bi bi-upload me-1"></i> Upload'))

class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired()])
    description = TextAreaField("Job Description", validators=[DataRequired()])
    requirements = TextAreaField("Job Requirements", validators=[DataRequired()])
    location = StringField("Location", validators=[DataRequired()])
    salary_range = StringField("Salary Range")
    status = SelectField("Status", choices=[("open", "Open"), ("closed", "Closed")], validators=[DataRequired()])
    closing_date = DateField("Closing Date", format="%Y-%m-%d", validators=[DataRequired()])
    submit = SubmitField(Markup('<i class="bi bi-briefcase me-1"></i> Submit Job Posting'))

class ApplicationForm(FlaskForm):
    resume = SelectField('Select Resume', coerce=int, validators=[DataRequired()])
    cover_letter = TextAreaField('Cover Letter', validators=[DataRequired(), Length(min=100, max=2000)])
    submit = SubmitField(Markup('<i class="bi bi-send me-1"></i> Submit Application'))

class InterviewForm(FlaskForm):
    interview_date = DateField('Interview Date', format='%Y-%m-%d', validators=[DataRequired()])
    interview_time = StringField('Interview Time (HH:MM)', validators=[DataRequired()])
    meeting_link = StringField('Meeting Link', validators=[DataRequired()])
    additional_notes = TextAreaField('Additional Notes')
    submit = SubmitField(Markup('<i class="bi bi-calendar-check me-1"></i> Schedule Interview'))

# Add forms for profile editing, job posting etc. later

