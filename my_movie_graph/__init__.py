import os
from flask import Flask

def create_app():
    """Creates and configures main driver for my_movie_graph"""
    app = Flask(__name__, instance_relative_config=True)
    app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

    # Confirm instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Temporary Hello World page
    from . import hello
    app.register_blueprint(hello.bp)

    return app