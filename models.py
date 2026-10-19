from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Operator(db.Model):
    __tablename__ = "operators"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Operator {self.name}>"

class DailyRecord(db.Model):
    __tablename__ = "daily_records"

    id = db.Column(db.Integer, primary_key=True)

    operator_id = db.Column(
        db.Integer,
        db.ForeignKey("operators.id"),
        nullable=False
    )

    date = db.Column(db.Date, nullable=False)

    calls_handled = db.Column(
        db.Integer,
        nullable=False
    )

    cancellations = db.Column(
        db.Integer,
        nullable=False
    )

    retentions = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    operator = db.relationship(
        "Operator",
        backref="daily_records"
    )

class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)

    retention_target = db.Column(
        db.Float,
        nullable=False,
        default=85.0
    )