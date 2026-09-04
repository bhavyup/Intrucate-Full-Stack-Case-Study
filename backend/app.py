from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from routes.ask import ask_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(ask_bp)
    return app


if __name__ == "__main__":
    # debug is fine locally, a real deployment would sit behind a proper WSGI server
    create_app().run(port=5000, debug=True)
