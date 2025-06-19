import os
from pdfminer.high_level import extract_text
from docx import Document
import logging
from werkzeug.utils import secure_filename
import uuid
from flask import current_app, render_template
from flask_mail import Message, Mail
import tempfile
from PIL import Image
import io
import base64
from werkzeug.security import generate_password_hash as werkzeug_generate_password_hash
from werkzeug.security import check_password_hash as werkzeug_check_password_hash
import hashlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

mail = Mail()

def parse_resume(file_path):
    """Parses text content from PDF or DOCX files."""
    _, file_extension = os.path.splitext(file_path)
    text = ""
    try:
        if file_extension.lower() == ".pdf":
            logger.info(f"Parsing PDF: {file_path}")
            text = extract_text(file_path)
            logger.info(f"Successfully parsed PDF: {file_path}")
        elif file_extension.lower() == ".docx":
            logger.info(f"Parsing DOCX: {file_path}")
            document = Document(file_path)
            full_text = []
            for para in document.paragraphs:
                full_text.append(para.text)
            text = "\n".join(full_text)
            logger.info(f"Successfully parsed DOCX: {file_path}")
        elif file_path.lower().endswith('.txt'):
            # Read text files directly
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            logger.warning(f"Unsupported file type: {file_extension} for file {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}", exc_info=True)
        return None
    return text.strip() if text else None

def save_profile_image(file):
    """Save a profile image and return the filename."""
    if not file:
        return None
    
    try:
        # Use img directory for profile images
        profile_images_path = os.path.join(current_app.static_folder, 'img')
        os.makedirs(profile_images_path, exist_ok=True)
        
        # Generate a unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        file_path = os.path.join(profile_images_path, unique_filename)
        
        # Save the file
        file.save(file_path)
        logger.info(f"Profile image saved to {file_path}")
        
        # Return just the filename (not the full path)
        return unique_filename
    except Exception as e:
        logger.error(f"Error saving profile image: {e}", exc_info=True)
        return None

def send_email(to, subject, template, **kwargs):
    """Send an email using Flask-Mail."""
    msg = Message(
        subject,
        recipients=[to],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    msg.html = render_template(template, **kwargs)
    mail.send(msg)

def show_pdf(file_path):
    """Display a PDF file using base64 encoding and HTML iframe."""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
        return pdf_display
    except Exception as e:
        logger.error(f"Error displaying PDF {file_path}: {e}", exc_info=True)
        return None

def generate_unique_filename(original_filename):
    """Generate a unique filename by prefixing a UUID to the original filename."""
    ext = os.path.splitext(original_filename)[1] if original_filename else ''
    return str(uuid.uuid4()) + '_' + secure_filename(original_filename)

def save_uploaded_file(uploaded_file, directory):
    """Save an uploaded file to the specified directory with a unique filename."""
    if not uploaded_file:
        return None
    
    unique_filename = generate_unique_filename(uploaded_file.filename)
    file_path = os.path.join(directory, unique_filename)
    
    try:
        uploaded_file.save(file_path)
        logger.info(f"Saved uploaded file to {file_path}")
        return unique_filename
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return None

# Custom password hashing functions that use sha256 instead of scrypt
def generate_password_hash(password):
    """Generate a SHA-256 password hash compatible with Python 3.13."""
    salt = os.urandom(16)  # 16 bytes of random salt
    password_bytes = password.encode('utf-8')
    salted_hash = hashlib.sha256(salt + password_bytes).hexdigest()
    # Store as algorithm:salt:hash
    return f"sha256:{base64.b64encode(salt).decode('utf-8')}:{salted_hash}"

def check_password_hash(stored_hash, password):
    """Check a password against a SHA-256 hash."""
    try:
        # Parse the stored hash
        algorithm, salt_b64, hash_value = stored_hash.split(':')
        
        # Check if this is a new-style hash
        if algorithm == 'sha256':
            salt = base64.b64decode(salt_b64)
            password_bytes = password.encode('utf-8')
            calculated_hash = hashlib.sha256(salt + password_bytes).hexdigest()
            return calculated_hash == hash_value
        else:
            # Fall back to werkzeug's implementation for old-style hashes
            return werkzeug_check_password_hash(stored_hash, password)
    except Exception:
        # If any error occurs, return False (invalid format)
        return False

