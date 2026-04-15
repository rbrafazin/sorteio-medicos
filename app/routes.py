from functools import wraps
from io import BytesIO
from secrets import randbelow
from urllib.parse import urljoin, urlsplit

import qrcode
from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from .forms import AdminLoginForm, RegistrationForm
from .models import DoctorRegistration, db


main_bp = Blueprint("main", __name__)


def generate_raffle_code() -> str:
    return f"MED-{randbelow(1_000_000):06d}"


def normalize_cpf(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def normalize_email(value: str) -> str:
    return value.strip().lower()


def build_storage_crm(
    tipo_participante: str, crm_number: str, crm_uf: str, cpf: str
) -> str:
    if tipo_participante == "medico":
        return f"{crm_number}-{crm_uf}"
    return f"EST-{cpf}"


def get_public_form_url() -> str:
    public_base_url = current_app.config.get("PUBLIC_BASE_URL", "")
    register_path = url_for("main.register")

    if public_base_url:
        return urljoin(f"{public_base_url}/", register_path.lstrip("/"))

    return url_for("main.register", _external=True)


def admin_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_authenticated"):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(
                    {"message": "Sua sessao expirou. Faca login novamente."}
                ), 401

            flash("Faca login para acessar o painel administrativo.", "warning")
            return redirect(url_for("main.admin_login", next=request.path))

        return view_func(*args, **kwargs)

    return wrapped_view


def is_safe_redirect_target(target: str | None) -> bool:
    if not target:
        return False

    target_parts = urlsplit(target)
    return not target_parts.netloc and target.startswith("/")


@main_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("main.admin_panel"))

    form = AdminLoginForm()

    if form.validate_on_submit():
        username = current_app.config["ADMIN_USERNAME"]
        plain_password = current_app.config.get("ADMIN_PASSWORD")
        password_hash = current_app.config["ADMIN_PASSWORD_HASH"]
        username_matches = form.username.data.strip() == username
        password_matches = False

        if plain_password is not None:
            password_matches = form.password.data == plain_password
        elif password_hash:
            password_matches = check_password_hash(password_hash, form.password.data)

        if username_matches and password_matches:
            session.clear()
            session["admin_authenticated"] = True
            flash("Login realizado com sucesso.", "success")
            next_url = request.args.get("next")
            if is_safe_redirect_target(next_url):
                return redirect(next_url)
            return redirect(url_for("main.admin_panel"))

        flash("Usuario ou senha invalidos.", "danger")

    return render_template("admin_login.html", form=form)


@main_bp.route("/admin/logout", methods=["POST"])
@admin_login_required
def admin_logout():
    session.clear()
    flash("Sessao encerrada com sucesso.", "info")
    return redirect(url_for("main.admin_login"))


@main_bp.route("/", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        tipo_participante = form.tipo_participante.data
        crm_number = form.crm.data.strip()
        crm_uf = form.uf.data.strip().upper()
        email = normalize_email(form.email.data)
        cpf = normalize_cpf(form.cpf.data)
        telefone = form.telefone.data.strip()
        crm = build_storage_crm(tipo_participante, crm_number, crm_uf, cpf)

        if (
            tipo_participante == "medico"
            and DoctorRegistration.query.filter_by(crm=crm).first()
        ):
            flash("Este CRM ja esta cadastrado no sorteio.", "danger")
            return render_template("index.html", form=form)

        if DoctorRegistration.query.filter_by(cpf=cpf).first():
            flash("Este CPF ja esta cadastrado no sorteio.", "danger")
            return render_template("index.html", form=form)

        raffle_code = generate_raffle_code()
        registration = DoctorRegistration(
            tipo_participante=tipo_participante,
            nome=form.nome.data.strip(),
            crm=crm,
            email=email,
            cpf=cpf,
            telefone=telefone,
            codigo_sorteio=raffle_code,
        )

        db.session.add(registration)

        try:
            db.session.commit()
            flash(
                f"Cadastro realizado com sucesso. Seu codigo do sorteio e {raffle_code}.",
                "success",
            )
            return redirect(url_for("main.register"))
        except IntegrityError:
            db.session.rollback()
            flash(
                "Nao foi possivel salvar o cadastro. Verifique CRM, CPF e categoria.",
                "danger",
            )

    return render_template("index.html", form=form)


@main_bp.route("/qrcode")
def qr_code_page():
    return render_template(
        "qrcode.html",
        form_url=get_public_form_url(),
        qr_image_url=url_for("main.qr_code_image"),
    )


@main_bp.route("/qrcode.png")
def qr_code_image():
    form_url = get_public_form_url()
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(form_url)
    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    return Response(buffer.getvalue(), mimetype="image/png")


@main_bp.route("/sorteio-admin")
@admin_login_required
def admin_panel():
    registrations = DoctorRegistration.query.order_by(
        DoctorRegistration.criado_em.desc()
    ).all()
    doctor_count = sum(
        1
        for registration in registrations
        if registration.tipo_participante == "medico"
    )
    student_count = sum(
        1
        for registration in registrations
        if registration.tipo_participante == "estudante"
    )
    return render_template(
        "admin.html",
        registrations=registrations,
        doctor_count=doctor_count,
        student_count=student_count,
    )


@main_bp.route("/sortear", methods=["POST"])
@admin_login_required
def draw_winner():
    tipo_participante = request.args.get("tipo", "").strip().lower()
    query = DoctorRegistration.query

    if tipo_participante in {"medico", "estudante"}:
        query = query.filter_by(tipo_participante=tipo_participante)

    total = query.count()

    if total == 0:
        if tipo_participante == "medico":
            message = "Nenhum medico cadastrado para realizar o sorteio."
        elif tipo_participante == "estudante":
            message = "Nenhum estudante cadastrado para realizar o sorteio."
        else:
            message = "Nenhum cadastro encontrado para realizar o sorteio."
        return jsonify({"message": message}), 404

    winner = query.order_by(func.random()).first()
    return jsonify(winner.to_dict())
