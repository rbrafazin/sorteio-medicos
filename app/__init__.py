import os

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .models import db

csrf = CSRFProtect()



def create_app() -> Flask:
    app = Flask(__name__)

    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("ERRO FATAL: Variável DATABASE_URL ausente. Por favor, forneça o link do banco PostgreSQL.")

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "troque-esta-chave-em-producao"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME", "admin"),
        ADMIN_PASSWORD=admin_password,
        ADMIN_PASSWORD_HASH=admin_password_hash,
        PUBLIC_BASE_URL=os.getenv("PUBLIC_BASE_URL", "").rstrip("/"),
    )

    db.init_app(app)
    csrf.init_app(app)

    from .routes import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app
