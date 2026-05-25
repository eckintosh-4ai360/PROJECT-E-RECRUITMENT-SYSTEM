from app import create_app

application = create_app()
app = application

if __name__ == "__main__":
    # This block is typically not executed when run by Gunicorn,
    # but can be useful for direct execution or debugging.
    # Use the configuration from run.py for running locally.
    application.run()

