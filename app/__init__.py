import os
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, text

from .models import db

csrf = CSRFProtect()


def ensure_schema_updates() -> None:
    inspector = inspect(db.engine)

    if not inspector.has_table("doctor_registrations"):
        return

    columns = {
        column["name"] for column in inspector.get_columns("doctor_registrations")
    }
    schema_changed = False

    if "email" not in columns:
        db.session.execute(
            text("ALTER TABLE doctor_registrations ADD COLUMN email VARCHAR(255)")
        )
        schema_changed = True

    if "cpf" not in columns:
        db.session.execute(
            text("ALTER TABLE doctor_registrations ADD COLUMN cpf VARCHAR(11)")
        )
        schema_changed = True

    if "tipo_participante" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE doctor_registrations "
                "ADD COLUMN tipo_participante VARCHAR(20) DEFAULT 'medico'"
            )
        )
        schema_changed = True

    if schema_changed:
        db.session.commit()

    db.session.execute(
        text(
            "UPDATE doctor_registrations "
            "SET tipo_participante = 'medico' "
            "WHERE tipo_participante IS NULL OR tipo_participante = ''"
        )
    )

    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_doctor_registrations_email "
            "ON doctor_registrations (email)"
        )
    )
    db.session.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_registrations_cpf "
            "ON doctor_registrations (cpf)"
        )
    )
    db.session.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_doctor_registrations_tipo_participante "
            "ON doctor_registrations (tipo_participante)"
        )
    )
    db.session.commit()


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
        ensure_schema_updates()

    return app
