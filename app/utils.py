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

logging.basicConfig(level=logging.INFO)
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
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(file_path)
    return unique_filename

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

