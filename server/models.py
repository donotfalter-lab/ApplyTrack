from datetime import datetime, timezone

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from config import bcrypt, db

VALID_STATUSES = ("applied", "interview", "offer", "rejected")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    applications = db.relationship(
        "Application", back_populates="user", cascade="all, delete-orphan"
    )

    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(
            password.encode("utf-8")
        ).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode("utf-8")
        )

    def to_dict(self):
        return {"id": self.id, "username": self.username}

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False, default="applied")
    job_description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="applications")
    responses = db.relationship(
        "Response", back_populates="application", cascade="all, delete-orphan"
    )

    @validates("company", "role")
    def validate_not_blank(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must not be empty.")
        return value.strip()

    @validates("status")
    def validate_status(self, key, value):
        if value not in VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(VALID_STATUSES)}.")
        return value

    @validates("job_description")
    def validate_job_description(self, key, value):
        if value is not None and not isinstance(value, str):
            raise ValueError("job_description must be text.")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "status": self.status,
            "job_description": self.job_description,
        }

    def __repr__(self):
        return f"<Application {self.id} {self.company} - {self.role}>"


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    generated_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    application_id = db.Column(
        db.Integer, db.ForeignKey("applications.id"), nullable=False
    )

    application = db.relationship("Application", back_populates="responses")

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "generated_text": self.generated_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "application_id": self.application_id,
        }

    def __repr__(self):
        return f"<Response {self.id} for Application {self.application_id}>"
