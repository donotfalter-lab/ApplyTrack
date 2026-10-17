from config import app, db  # noqa: F401
from models import Application, Response, User  # noqa: F401


@app.route("/")
def index():
    return {"message": "ApplyTrack API running"}


if __name__ == "__main__":
    app.run(port=5555, debug=True)
