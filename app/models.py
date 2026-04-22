from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class DoctorRegistration(db.Model):
    __tablename__ = "doctor_registrations"

    id = db.Column(db.Integer, primary_key=True)
    tipo_participante = db.Column(
        db.String(20), nullable=False, default="medico", index=True
    )
    nome = db.Column(db.String(120), nullable=False)
    crm = db.Column(db.String(20), nullable=True, unique=True, index=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    cpf = db.Column(db.String(11), nullable=False, unique=True, index=True)
    whatsapp = db.Column(db.String(20), nullable=False)
    codigo_sorteio = db.Column(db.String(40), nullable=False, unique=True, index=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def formatted_cpf(self) -> str:
        digits = "".join(char for char in (self.cpf or "") if char.isdigit())
        if len(digits) != 11:
            return self.cpf or "-"
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"

    @property
    def participant_type_label(self) -> str:
        if self.tipo_participante == "medico":
            return "Medico"
        if self.tipo_participante == "estudante":
            return "Estudante/Profissional da Saúde"
        return "Nao informado"

    @property
    def display_crm(self) -> str:
        return self.crm if self.tipo_participante == "medico" else "-"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo_participante": self.tipo_participante,
            "tipo_participante_label": self.participant_type_label,
            "nome": self.nome,
            "crm": self.display_crm,
            "email": self.email or "-",
            "cpf": self.formatted_cpf,
            "whatsapp": self.whatsapp,
            "codigo_sorteio": self.codigo_sorteio,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M"),
        }
