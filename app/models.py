from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class DoctorRegistration(db.Model):
    __tablename__ = "doctor_registrations"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    crm = db.Column(db.String(20), nullable=False, unique=True, index=True)
    telefone = db.Column(db.String(20), nullable=False)
    codigo_sorteio = db.Column(db.String(40), nullable=False, index=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "crm": self.crm,
            "telefone": self.telefone,
            "codigo_sorteio": self.codigo_sorteio,
            "criado_em": self.criado_em.strftime("%d/%m/%Y %H:%M"),
        }
