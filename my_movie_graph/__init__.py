import os
from flask import Flask

def create_app():
    """Creates and configures main driver for my_movie_graph"""
    app = Flask(__name__, instance_relative_config=True)

    # Confirm instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Associate path 'index' with path '/'
    #app.add_url_rule('/', endpoint='index')

    # Temporary Hello World page
    from . import hello
    app.register_blueprint(hello.bp)

    return app