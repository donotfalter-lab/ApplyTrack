from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from config import app, db, jwt
from models import Application, Response, User

MIN_PASSWORD_LENGTH = 8
APPLICATION_FIELDS = ("company", "role", "status", "job_description")


def error(message, status):
    return {"error": message}, status


def auth_payload(user):
    token = create_access_token(identity=str(user.id))
    return {"user": user.to_dict(), "token": token}


def current_user_id():
    return int(get_jwt_identity())


def json_body():
    """Return the request's JSON object, or None if it is missing or not a JSON object."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def owned_application(application_id):
    return Application.query.filter_by(
        id=application_id, user_id=current_user_id()
    ).first()


def newest_responses(application):
    return sorted(
        application.responses, key=lambda r: (r.created_at, r.id), reverse=True
    )


# ---------- Error handlers ----------

@app.errorhandler(404)
def not_found(e):
    return error("Not found", 404)


@app.errorhandler(ValueError)
def handle_value_error(e):
    db.session.rollback()
    return error(str(e), 400)


@jwt.unauthorized_loader
def missing_token(reason):
    return error("Missing authorization token", 401)


@jwt.invalid_token_loader
def invalid_token(reason):
    return error("Invalid token", 401)


@jwt.expired_token_loader
def expired_token(jwt_header, jwt_payload):
    return error("Token has expired", 401)


# ---------- Routes ----------

@app.route("/")
def index():
    return {"message": "ApplyTrack API running"}


@app.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if not isinstance(username, str) or not username.strip():
        return error("Username is required", 400)
    if not isinstance(password, str) or not password:
        return error("Password is required", 400)
    if len(password) < MIN_PASSWORD_LENGTH:
        return error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters", 400)

    username = username.strip()
    if User.query.filter_by(username=username).first():
        return error("Username is already taken", 409)

    user = User(username=username)
    user.password_hash = password
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("Username is already taken", 409)
    except Exception:
        db.session.rollback()
        raise

    return auth_payload(user), 201


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")

    if isinstance(username, str) and isinstance(password, str):
        user = User.query.filter_by(username=username.strip()).first()
        if user and user.authenticate(password):
            return auth_payload(user), 200

    return error("Invalid username or password", 401)


@app.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return error("User not found", 404)
    return user.to_dict(), 200



@app.get("/applications")
@jwt_required()
def list_applications():
    applications = (
        Application.query.filter_by(user_id=current_user_id())
        .order_by(Application.id.desc())
        .all()
    )
    return [a.to_dict() for a in applications], 200


@app.post("/applications")
@jwt_required()
def create_application():
    data = json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)

    fields = {k: data[k] for k in APPLICATION_FIELDS if k in data}
    for required in ("company", "role"):
        fields.setdefault(required, None)

    application = Application(**fields, user_id=current_user_id())
    db.session.add(application)
    commit()
    return application.to_dict(), 201


@app.get("/applications/<int:application_id>")
@jwt_required()
def get_application(application_id):
    application = owned_application(application_id)
    if not application:
        return error("Not found", 404)
    return {
        **application.to_dict(),
        "responses": [r.to_dict() for r in newest_responses(application)],
    }, 200


@app.patch("/applications/<int:application_id>")
@jwt_required()
def update_application(application_id):
    application = owned_application(application_id)
    if not application:
        return error("Not found", 404)

    data = json_body()
    if data is None:
        return error("Request body must be a JSON object", 400)

    disallowed = sorted(set(data) - set(APPLICATION_FIELDS))
    if disallowed:
        return error(f"Cannot update field(s): {', '.join(disallowed)}", 400)
    if not data:
        return error(f"Provide at least one of: {', '.join(APPLICATION_FIELDS)}", 400)

    for key, value in data.items():
        setattr(application, key, value)
    commit()
    return application.to_dict(), 200


@app.delete("/applications/<int:application_id>")
@jwt_required()
def delete_application(application_id):
    application = owned_application(application_id)
    if not application:
        return error("Not found", 404)
    db.session.delete(application)
    commit()
    return "", 204


@app.get("/applications/<int:application_id>/responses")
@jwt_required()
def list_responses(application_id):
    application = owned_application(application_id)
    if not application:
        return error("Not found", 404)
    return [r.to_dict() for r in newest_responses(application)], 200


@app.delete("/responses/<int:response_id>")
@jwt_required()
def delete_response(response_id):
    response = (
        Response.query.join(Application)
        .filter(Response.id == response_id, Application.user_id == current_user_id())
        .first()
    )
    if not response:
        return error("Not found", 404)
    db.session.delete(response)
    commit()
    return "", 204


if __name__ == "__main__":
    app.run(port=5555, debug=True)
