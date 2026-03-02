from flask import Flask
from flask_cors import CORS
from config import Config
import responses


def create_app(config=None):
    app = Flask(__name__)
    CORS(app)

    if config is None:
        config = Config()

    from database import init_db, create_tables
    init_db(app, config)
    create_tables()

    from controllers.authentication import ent
    from controllers.authorization import ori
    from controllers.oauth import ope
    app.register_blueprint(ent)
    app.register_blueprint(ori)
    app.register_blueprint(ope)

    @app.route('/')
    def index():
        return responses.success('autheo v3 is alive!')

    app.config['AUTHEO_CONFIG'] = config
    return app


if __name__ == '__main__':
    config = Config()
    app = create_app(config)
    if config.DEBUG:
        app.run(port=config.PORT, host=config.HOST, debug=True)
    else:
        from waitress import serve
        serve(app, port=config.PORT, host=config.HOST)
