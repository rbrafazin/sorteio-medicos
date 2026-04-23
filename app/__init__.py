import os

from flask import Flask, flash, jsonify, redirect, request, session, url_for
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect

from .models import db

csrf = CSRFProtect()



def create_app() -> Flask:
    app = Flask(__name__)

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise ValueError("ERRO FATAL: Variável SECRET_KEY ausente. Defina uma chave secreta forte.")

    admin_username = os.getenv("ADMIN_USERNAME")
    if not admin_username:
        raise ValueError("ERRO FATAL: Variável ADMIN_USERNAME ausente. Defina o nome do usuário administrativo.")

    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    if not admin_password and not admin_password_hash:
        raise ValueError(
            "ERRO FATAL: Nenhuma credencial de senha configurada. "
            "Defina ADMIN_PASSWORD ou ADMIN_PASSWORD_HASH."
        )

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("ERRO FATAL: Variável DATABASE_URL ausente. Por favor, forneça o link do banco PostgreSQL.")

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=secret_key,
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        ADMIN_USERNAME=admin_username,
        ADMIN_PASSWORD=admin_password,
        ADMIN_PASSWORD_HASH=admin_password_hash,
        PUBLIC_BASE_URL=os.getenv("PUBLIC_BASE_URL", "").rstrip("/"),
    )

    db.init_app(app)
    csrf.init_app(app)

    from .routes import main_bp

    app.register_blueprint(main_bp)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error: CSRFError):
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        admin_session_active = bool(session.get("admin_authenticated"))

        if is_ajax:
            if not admin_session_active:
                return jsonify({"message": "Sua sessao expirou. Faca login novamente."}), 401
            return (
                jsonify(
                    {
                        "message": (
                            "Nao foi possivel validar a requisicao. "
                            "Atualize a pagina e tente novamente."
                        )
                    }
                ),
                400,
            )

        flash("Sua sessao expirou ou o formulario ficou invalido. Tente novamente.", "warning")
        if request.path.startswith("/admin") or request.path.startswith("/sortear"):
            return redirect(url_for("main.admin_login"))
        return redirect(url_for("main.register"))

    with app.app_context():
        db.create_all()

    return app
