import os
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .models import db

csrf = CSRFProtect()


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    database_path = os.path.join(app.instance_path, "sorteio.db")

    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "troque-esta-chave-em-producao"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{database_path}"),
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
