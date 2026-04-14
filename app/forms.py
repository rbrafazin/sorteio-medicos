from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class RegistrationForm(FlaskForm):
    nome = StringField(
        "Nome",
        validators=[
            DataRequired(message="Informe o nome do médico."),
            Length(min=3, max=120, message="O nome deve ter entre 3 e 120 caracteres."),
        ],
        render_kw={"placeholder": "Dr(a). Nome Sobrenome"},
    )
    crm = StringField(
        "CRM",
        validators=[
            DataRequired(message="Informe o CRM."),
            Length(min=4, max=20, message="O CRM deve ter entre 4 e 20 caracteres."),
            Regexp(
                r"^[A-Za-z0-9/\-\.]+$",
                message="Use apenas letras, números e os caracteres / - .",
            ),
        ],
        render_kw={"placeholder": "123456-SP"},
    )
    telefone = StringField(
        "Telefone",
        validators=[
            DataRequired(message="Informe o telefone."),
            Length(min=10, max=20, message="O telefone deve ter entre 10 e 20 caracteres."),
            Regexp(
                r"^[0-9()\-\+\s]+$",
                message="Use apenas números, espaços e os caracteres () - +",
            ),
        ],
        render_kw={"placeholder": "(11) 99999-0000"},
    )
    submit = SubmitField("Confirmar Cadastro")


class AdminLoginForm(FlaskForm):
    username = StringField(
        "Usuario",
        validators=[
            DataRequired(message="Informe o usuario administrador."),
            Length(min=3, max=80, message="O usuario deve ter entre 3 e 80 caracteres."),
        ],
        render_kw={"placeholder": "admin"},
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe a senha."),
            Length(min=6, max=128, message="A senha deve ter entre 6 e 128 caracteres."),
        ],
        render_kw={"placeholder": "Sua senha"},
    )
    submit = SubmitField("Entrar no Painel")
