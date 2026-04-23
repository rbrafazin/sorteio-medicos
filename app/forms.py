from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class RegistrationForm(FlaskForm):
    PARTICIPANT_TYPE_CHOICES = [
        ("", "Escolha..."),
        ("medico", "Médico"),
        ("estudante", "Estudante/Profissional da Saúde"),
    ]
    UF_CHOICES = [
        ("", "UF..."),
        ("AC", "AC"),
        ("AL", "AL"),
        ("AP", "AP"),
        ("AM", "AM"),
        ("BA", "BA"),
        ("CE", "CE"),
        ("DF", "DF"),
        ("ES", "ES"),
        ("GO", "GO"),
        ("MA", "MA"),
        ("MT", "MT"),
        ("MS", "MS"),
        ("MG", "MG"),
        ("PA", "PA"),
        ("PB", "PB"),
        ("PR", "PR"),
        ("PE", "PE"),
        ("PI", "PI"),
        ("RJ", "RJ"),
        ("RN", "RN"),
        ("RS", "RS"),
        ("RO", "RO"),
        ("RR", "RR"),
        ("SC", "SC"),
        ("SP", "SP"),
        ("SE", "SE"),
        ("TO", "TO"),
    ]

    tipo_participante = SelectField(
        "Categoria",
        choices=PARTICIPANT_TYPE_CHOICES,
        validators=[DataRequired(message="Selecione a categoria.")],
    )
    nome = StringField(
        "Nome",
        validators=[
            DataRequired(message="Informe o nome."),
            Length(min=3, max=120, message="O nome deve ter entre 3 e 120 caracteres."),
        ],
        render_kw={
            "placeholder": "Nome completo",
            "autocomplete": "name",
        },
    )
    crm = StringField(
        "CRM",
        validators=[
            Optional(),
            Length(min=4, max=10, message="O CRM deve ter entre 4 e 10 digitos."),
            Regexp(
                r"^\d+$",
                message="Use apenas numeros no CRM.",
            ),
        ],
        render_kw={
            "placeholder": "123456",
            "inputmode": "numeric",
            "autocomplete": "off",
        },
    )
    uf = SelectField(
        "UF",
        choices=UF_CHOICES,
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Informe o email."),
            Length(max=255, message="O email deve ter no maximo 255 caracteres."),
            Regexp(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                message="Informe um email valido.",
            ),
        ],
        render_kw={
            "placeholder": "nome@exemplo.com",
            "inputmode": "email",
            "autocomplete": "email",
            "autocapitalize": "off",
        },
    )
    cpf = StringField(
        "CPF",
        validators=[
            DataRequired(message="Informe o CPF."),
            Regexp(
                r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$",
                message="Informe um CPF valido com 11 digitos.",
            ),
        ],
        render_kw={
            "placeholder": "000.000.000-00",
            "inputmode": "numeric",
            "autocomplete": "off",
            "maxlength": 14,
        },
    )
    whatsapp = StringField(
        "WhatsApp",
        validators=[
            DataRequired(message="Informe o WhatsApp."),
            Length(
                min=10, max=20, message="O WhatsApp deve ter entre 10 e 20 caracteres."
            ),
            Regexp(
                r"^[0-9()\-\+\s]+$",
                message="Use apenas numeros, espacos e os caracteres () - +",
            ),
        ],
        render_kw={
            "placeholder": "(11) 99999-0000",
            "inputmode": "tel",
            "autocomplete": "tel",
            "maxlength": 15,
        },
    )
    submit = SubmitField("Confirmar Cadastro")

    def validate(self, extra_validators=None):
        is_valid = super().validate(extra_validators=extra_validators)

        if self.tipo_participante.data == "medico":
            if not (self.crm.data or "").strip():
                self.crm.errors.append("Informe o numero do CRM.")
                is_valid = False

            if not (self.uf.data or "").strip():
                self.uf.errors.append("Selecione a UF do CRM.")
                is_valid = False

        return is_valid


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Usuario",
        validators=[
            DataRequired(message="Informe o usuario administrador."),
            Length(
                min=3, max=80, message="O usuario deve ter entre 3 e 80 caracteres."
            ),
        ],
        render_kw={"placeholder": "admin"},
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe a senha."),
            Length(
                min=6, max=128, message="A senha deve ter entre 6 e 128 caracteres."
            ),
        ],
        render_kw={"placeholder": "Sua senha"},
    )
    submit = SubmitField("Entrar no Painel")
