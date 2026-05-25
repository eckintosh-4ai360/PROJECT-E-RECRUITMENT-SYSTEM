from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, FileField, TextAreaField, DateField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
from app.models import User, UserRole
from flask_wtf.file import FileAllowed
from markupsafe import Markup
import logging

logger = logging.getLogger(__name__)

class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., johndoe"
        })
    email = StringField("Email", validators=[DataRequired(), Email()], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., john.doe@example.com"
        })
    first_name = StringField("First Name", validators=[DataRequired()], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., John"
        })
    last_name = StringField("Last Name", validators=[DataRequired()], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., Doe"
        })
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., +233 24 123 4567"
        })
    profile_image = FileField("Profile Image", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        })
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "Create a secure password"
        })
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")], 
    render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px;  color: green",
            "placeholder": "Confirm your password"
        })
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
    username = StringField("Username", validators=[DataRequired(), Length(min=4, max=25)], render_kw={"placeholder": "e.g., johndoe"})
    email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"placeholder": "e.g., john.doe@example.com"})
    first_name = StringField("First Name", validators=[DataRequired()], render_kw={"placeholder": "e.g., John"})
    last_name = StringField("Last Name", validators=[DataRequired()], render_kw={"placeholder": "e.g., Doe"})
    phone_number = StringField("Phone Number", validators=[DataRequired(), Length(min=10, max=15)], render_kw={"placeholder": "e.g., +233 24 123 4567"})
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
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "e.g., john.doe@example.com"
        }
 )
    password = PasswordField("Password", validators=[DataRequired()], 
            render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "Enter your password"
        })
    remember_me = BooleanField("Remember Me", )
    submit = SubmitField("Sign In")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        
    def validate(self):
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            logger.info("===DEBUG=== Form validation failed")
            return False
            
        if self.email.data:
            logger.info(f"===DEBUG=== Form validation - Email length: {len(self.email.data)}")
        if self.password.data:
            logger.info(f"===DEBUG=== Form validation - Password length: {len(self.password.data)}")
        
        # Ensure password field is not empty
        if not self.password.data or not self.password.data.strip():
            logger.info("===DEBUG=== Empty password submitted")
            self.password.errors = ["Password cannot be empty"]
            return False
            
        return True

class ResumeUploadForm(FlaskForm):
    resume_file = FileField("Upload Resume", validators=[
        DataRequired(),
        FileAllowed(["pdf", "docx"], "Only PDF and DOCX files are allowed!")
    ])
    is_primary = BooleanField("Set as primary resume")

class JobForm(FlaskForm):
    title = StringField("Job Title", validators=[DataRequired()], render_kw={"placeholder": "e.g., Senior Software Engineer"})
    department = StringField("Department", validators=[DataRequired()], render_kw={"placeholder": "e.g., Computer Science / IT"})
    description = TextAreaField("Job Description", validators=[DataRequired()], render_kw={"placeholder": "Describe the responsibilities, role expectations, and daily tasks..."})
    required_skills = TextAreaField("Required Skills", validators=[DataRequired()], render_kw={"placeholder": "e.g., Python, Flask, SQL, Git, AWS (one per line or comma-separated)"})
    location = StringField("Location", validators=[DataRequired()], render_kw={"placeholder": "e.g., Tarkwa, Ghana or Remote"})
    salary_range = StringField("Salary Range", render_kw={"placeholder": "e.g., GHS 5,000 - 8,000 per month"})
    status = SelectField("Status", choices=[("open", "Open"), ("closed", "Closed")], validators=[DataRequired()])
    closing_date = DateField("Closing Date", format="%Y-%m-%d", validators=[DataRequired()], render_kw={"placeholder": "YYYY-MM-DD"})
    submit = SubmitField("Submit Job Posting")

class ApplicationForm(FlaskForm):
    resume = SelectField('Select Resume', coerce=int, validators=[DataRequired()])
    cover_letter = TextAreaField('Cover Letter', validators=[Optional()],
                               render_kw={"rows": 6, "placeholder": "Type your cover letter here..."})
    cover_letter_file = FileField('Upload Cover Letter (PDF, DOC, DOCX)', 
                                validators=[Optional(), FileAllowed(['pdf', 'doc', 'docx'])])
    submit = SubmitField('Submit Application', render_kw={"class": "btn-primary", "data-icon": "bi-send"})

    def validate(self):
        if not super().validate():
            return False
        if not self.cover_letter.data and not self.cover_letter_file.data:
            self.cover_letter.errors.append('Please provide a cover letter - either type it or upload a file.')
            return False
        return True

class InterviewForm(FlaskForm):
    interview_date = DateField('Interview Date', format='%Y-%m-%d', validators=[DataRequired()])
    interview_time = StringField('Interview Time (HH:MM)', validators=[DataRequired()], render_kw={"placeholder": "e.g., 10:00 AM or 14:30"})
    interview_level = SelectField('Interview Level', choices=[
        ('department', 'Department Level'),
        ('faculty', 'Faculty Level'),
        ('university', 'University Level')
    ], validators=[DataRequired()])
    interview_type = SelectField('Interview Type', choices=[
        ('online', 'Online / Video Conference'),
        ('phone', 'Phone Interview'),
        ('in-person', 'In-Person Interview')
    ], validators=[DataRequired()])
    location_or_link = StringField('Location or Meeting Link', validators=[DataRequired()], render_kw={"placeholder": "e.g., Google Meet Link or Room 402, Main Block"})
    interviewer = SelectField('Interviewer', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Additional Notes', render_kw={"placeholder": "e.g., Remind the candidate to prepare a 10-minute presentation."})
    submit = SubmitField('Schedule Interview')

    def __init__(self, *args, **kwargs):
        super(InterviewForm, self).__init__(*args, **kwargs)
        # Dynamically load admin users as potential interviewers
        from app.models import User, UserRole
        admins = User.query.filter_by(role=UserRole.admin).all()
        self.interviewer.choices = [(admin.id, f"{admin.first_name} {admin.last_name}") for admin in admins]

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(max=255)], 
                         render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "placeholder": "Enter event title"
        })
    description = TextAreaField('Event Description', validators=[DataRequired()], 
                              render_kw={"rows": 5, "placeholder": "Describe the event details...", 
                                         "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"})
    event_date = DateTimeField('Event Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()],
                                render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green",
            "type": "datetime-local"
        })
    location = StringField('Event Location', validators=[Optional(), Length(max=255)],
                         render_kw={"placeholder": "Enter event location or 'Online'", 
                                    "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"})
    event_type = SelectField('Event Type', choices=[
        ('general', 'General'),
        ('academic', 'Academic'),
        ('career', 'Career'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('social', 'Social')
    ], validators=[DataRequired()], 
                              render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    status = SelectField('Event Status', choices=[
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()], default='upcoming', 
                          render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    image = FileField('Event Image', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ], 
                       render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    video = FileField('Event Video', validators=[
        Optional(),
        FileAllowed(['mp4', 'avi', 'mov', 'wmv'], 'Videos only!')
    ], 
                       render_kw={
            "style": "border: 1px solid #22c55e; border-radius: 4px; padding: 8px; color: green"
        ,})
    submit = SubmitField('Create Event',  render_kw={"class": "btn-primary", "data-icon": "bi-send"})

# Add forms for profile editing, job posting etc. later

