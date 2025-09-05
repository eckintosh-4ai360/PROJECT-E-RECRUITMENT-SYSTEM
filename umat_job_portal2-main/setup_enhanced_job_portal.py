"""
Setup script for installing enhanced job portal dependencies
"""
import os
import subprocess
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command):
    """Run a shell command and log output"""
    logger.info(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stderr:
            logger.error(e.stderr)
        return False

def setup_environment():
    """Setup the Python environment"""
    logger.info("Setting up environment...")
    
    # Check if virtual environment exists
    if not os.path.exists("venv"):
        logger.info("Creating virtual environment...")
        if not run_command("python -m venv venv"):
            logger.error("Failed to create virtual environment")
            return False
    
    # Activate virtual environment and install dependencies
    if sys.platform.startswith('win'):
        activate_cmd = ".\\venv\\Scripts\\activate"
        pip_cmd = ".\\venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "./venv/bin/pip"
    
    logger.info("Installing dependencies...")
    if not run_command(f"{pip_cmd} install --upgrade pip"):
        logger.warning("Failed to upgrade pip, continuing anyway...")
    
    if not run_command(f"{pip_cmd} install -r requirements.txt"):
        logger.error("Failed to install dependencies")
        return False
    
    # Install spaCy model
    logger.info("Installing spaCy language model...")
    if not run_command(f"{pip_cmd} install spacy"):
        logger.error("Failed to install spaCy")
        return False
    
    if not run_command(f"{activate_cmd} && python -m spacy download en_core_web_md"):
        logger.warning("Failed to download spaCy model, you may need to install it manually")
    
    return True

def setup_database():
    """Setup the database"""
    logger.info("Setting up database...")
    if run_command("flask db init"):
        if run_command("flask db migrate"):
            if run_command("flask db upgrade"):
                return True
    logger.error("Database setup failed")
    return False

def main():
    """Main setup function"""
    logger.info("Starting enhanced job portal setup...")
    
    if setup_environment():
        logger.info("Environment setup complete!")
    else:
        logger.error("Environment setup failed")
        return
    
    logger.info("\nSetup completed successfully!")
    logger.info("\nTo start the application:")
    if sys.platform.startswith('win'):
        logger.info("1. Activate the virtual environment: .\\venv\\Scripts\\activate")
    else:
        logger.info("1. Activate the virtual environment: source venv/bin/activate")
    logger.info("2. Start the server: flask run")
    logger.info("\nEnjoy your enhanced job portal with advanced NLP features!")

if __name__ == "__main__":
    main() 