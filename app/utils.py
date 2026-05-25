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
        # Use profile_images directory for profile images
        profile_images_path = os.path.join(current_app.static_folder, 'profile_images')
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

def send_email(subject, recipients, template, **kwargs):
    """
    Send an email using Flask-Mail with better error handling.
    
    Args:
        subject (str): Email subject
        recipients (list): List of email addresses
        template (str): Path to the email template
        **kwargs: Additional parameters to pass to the template
    """
    try:
        msg = Message(
            subject,
            recipients=recipients,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@umat.edu.gh')
        )
        msg.html = render_template(template, **kwargs)
        
        # Check if mail configuration is set
        if not current_app.config.get('MAIL_SERVER'):
            logger.warning("Mail server not configured. Email would have been sent to: %s", recipients)
            logger.info("Email content: Subject: %s, Template: %s", subject, template)
            
            # Create a fallback mechanism for development
            logger.info("Creating fallback email preview file")
            preview_dir = os.path.join(current_app.root_path, 'temp_mail')
            os.makedirs(preview_dir, exist_ok=True)
            
            # Save the email content to a file for preview
            preview_file = os.path.join(preview_dir, f"email_{uuid.uuid4().hex}.html")
            with open(preview_file, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {subject}\n")
                f.write(f"To: {', '.join(recipients)}\n")
                f.write(f"From: {msg.sender}\n\n")
                f.write(msg.html)
            
            logger.info("Email preview saved to: %s", preview_file)
            return False
        
        # Send the actual email
        mail.send(msg)
        logger.info("Email sent successfully to %s", recipients)
        return True
    except Exception as e:
        logger.error("Failed to send email: %s", str(e), exc_info=True)
        return False

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
    try:
        salt = os.urandom(16)  # 16 bytes of random salt
        password_bytes = password.encode('utf-8')
        
        # Convert salt to hex
        salt_hex = salt.hex()
        
        # Create salted hash
        salted_hash = hashlib.sha256(salt + password_bytes).hexdigest()
        
        # Final format: salt_hex:hash_hex
        return f"{salt_hex}:{salted_hash}"
    except Exception as e:
        logger.error("Error generating password hash: %s", e)
        raise

def check_password_hash(stored_hash, password):
    """Check a password against a SHA-256 hash."""
    try:
        # Parse the stored hash
        parts = stored_hash.split(':')
        if len(parts) != 2:
            return False
            
        salt_hex, hash_value = parts
        
        # Convert salt from hex back to bytes
        salt = bytes.fromhex(salt_hex)
        
        # Create the hash with the same salt
        password_bytes = password.encode('utf-8')
        
        # Create the combined bytes
        combined = salt + password_bytes
        calculated_hash = hashlib.sha256(combined).hexdigest()
        return calculated_hash == hash_value
    except Exception as e:
        logger.error("Error checking password hash: %s", e, exc_info=True)
        return False

