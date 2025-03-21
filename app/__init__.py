from flask import Flask

def create_app():
    app = Flask(__name__)

    # Load cấu hình
    app.config.from_object('config.Config')

    # Import blueprint bên trong để tránh vòng lặp import
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
