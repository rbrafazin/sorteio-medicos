import csv
from datetime import datetime
from functools import wraps
from io import BytesIO
from io import StringIO
import re
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


def generate_raffle_code(tipo_participante: str) -> str:
    prefix = "MED" if tipo_participante == "medico" else "EST"
    return f"{prefix}-{randbelow(1_000_000):06d}"


def normalize_cpf(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def normalize_email(value: str) -> str:
    return value.strip().lower()


def get_integrity_error_message(error: IntegrityError) -> str:
    error_text = str(getattr(error, "orig", error)).lower()

    duplicate_messages = [
        ("cpf", "Este CPF ja esta cadastrado no sorteio."),
        ("crm", "Este CRM ja esta cadastrado no sorteio."),
        ("email", "Este email ja esta cadastrado no sorteio."),
        (
            "codigo_sorteio",
            "Nao foi possivel gerar um codigo unico agora. Tente novamente.",
        ),
    ]

    duplicate_key_match = re.search(r"key \(([^)]+)\)=", error_text)
    if duplicate_key_match:
        duplicated_field = duplicate_key_match.group(1).strip().lower()
        for field_name, message in duplicate_messages:
            if duplicated_field == field_name:
                return message

    if "duplicate" in error_text or "unique constraint" in error_text:
        for field_name, message in duplicate_messages:
            if field_name in error_text:
                return message
        return "Ja existe um cadastro com um dado unico repetido."

    null_column_match = re.search(r'null value in column "([^"]+)"', error_text)
    if null_column_match:
        column_name = null_column_match.group(1).strip().lower()
        if column_name == "crm":
            return (
                "O banco atual ainda exige CRM para este cadastro. "
                "Isso costuma indicar estrutura antiga no banco."
            )
        if column_name == "email":
            return (
                "O banco atual esta exigindo email de um jeito diferente do esperado. "
                "Verifique a estrutura da tabela."
            )
        return (
            f"O banco esta exigindo o campo {column_name}. "
            "Verifique se a estrutura da tabela esta atualizada."
        )

    return "Nao foi possivel salvar o cadastro. Verifique os dados informados."


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
    return redirect(url_for("main.admin_login"))


@main_bp.route("/", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        tipo_participante = form.tipo_participante.data
        crm_number = (form.crm.data or "").strip()
        crm_uf = (form.uf.data or "").strip().upper()
        email = normalize_email(form.email.data)
        cpf = normalize_cpf(form.cpf.data)
        whatsapp = form.whatsapp.data.strip()

        crm = f"{crm_number}-{crm_uf}" if tipo_participante == "medico" else None

        if (
            tipo_participante == "medico"
            and DoctorRegistration.query.filter_by(crm=crm).first()
        ):
            flash("Este CRM ja esta cadastrado no sorteio.", "danger")
            return render_template("index.html", form=form)

        if DoctorRegistration.query.filter_by(cpf=cpf).first():
            flash("Este CPF ja esta cadastrado no sorteio.", "danger")
            return render_template("index.html", form=form)

        raffle_code = generate_raffle_code(tipo_participante)
        while DoctorRegistration.query.filter_by(codigo_sorteio=raffle_code).first():
            raffle_code = generate_raffle_code(tipo_participante)

        registration = DoctorRegistration(
            tipo_participante=tipo_participante,
            nome=form.nome.data.strip(),
            crm=crm,
            email=email,
            cpf=cpf,
            whatsapp=whatsapp,
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
        except IntegrityError as error:
            db.session.rollback()
            current_app.logger.exception("Erro de integridade ao salvar cadastro")
            flash(get_integrity_error_message(error), "danger")

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
    drawn_count = sum(1 for registration in registrations if registration.already_drawn)
    return render_template(
        "admin.html",
        registrations=registrations,
        doctor_count=doctor_count,
        student_count=student_count,
        drawn_count=drawn_count,
    )


@main_bp.route("/admin/exportar-inscritos.csv")
@admin_login_required
def export_registrations_csv():
    registrations = DoctorRegistration.query.order_by(
        DoctorRegistration.criado_em.desc()
    ).all()

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=";")
    writer.writerow(
        [
            "ID",
            "Categoria",
            "Nome",
            "CRM",
            "Email",
            "CPF",
            "WhatsApp",
            "Codigo do Sorteio",
            "Cadastrado em",
            "Status do Sorteio",
            "Sorteado em",
        ]
    )

    for registration in registrations:
        writer.writerow(
            [
                registration.id,
                registration.participant_type_label,
                registration.nome,
                registration.display_crm,
                registration.email or "",
                registration.formatted_cpf,
                registration.whatsapp,
                registration.codigo_sorteio,
                registration.criado_em.strftime("%d/%m/%Y %H:%M"),
                registration.draw_status_label,
                registration.formatted_sorteado_em,
            ]
        )

    filename = f"inscritos-sorteio-{datetime.now().strftime('%Y%m%d-%H%M')}.csv"
    csv_content = "\ufeff" + csv_buffer.getvalue()

    return Response(
        csv_content,
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@main_bp.route("/sortear", methods=["POST"])
@admin_login_required
def draw_winner():
    tipo_participante = request.args.get("tipo", "").strip().lower()
    eligible_query = DoctorRegistration.query.filter(
        DoctorRegistration.sorteado_em.is_(None)
    )

    if tipo_participante in {"medico", "estudante"}:
        eligible_query = eligible_query.filter_by(tipo_participante=tipo_participante)

    total = eligible_query.count()

    if total == 0:
        if tipo_participante == "medico":
            message = (
                "Nenhum medico disponivel para sorteio. "
                "Todos ja foram sorteados ou nao ha cadastros."
            )
        elif tipo_participante == "estudante":
            message = "Nenhum estudante/profissional da saúde cadastrado para realizar o sorteio."
        else:
            message = "Nenhum cadastro disponivel para realizar o sorteio."
        return jsonify({"message": message}), 404

    winner = eligible_query.order_by(func.random()).first()
    winner.sorteado_em = datetime.utcnow()
    db.session.commit()
    return jsonify(winner.to_dict())
