# ApplyTrack

A full-stack job application tracker: Flask + SQLAlchemy backend, React frontend, JWT auth.

## Backend setup

```bash
cd server
pipenv install
pipenv shell
```

Create `server/.env` with a secret key:

```
JWT_SECRET_KEY=<random value>
```

Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`.

Set up the database and run the server:

```bash
flask db upgrade
flask run --port 5555   # or: python app.py
```

`GET /` returns `{"message": "ApplyTrack API running"}`.

## Models

- **User** — `id`, `username` (unique), hashed password. Has many applications.
- **Application** — `id`, `company`, `role`, `status` (`applied` | `interview` | `offer` | `rejected`), `job_description`, `user_id`. Has many responses.
- **Response** — `id`, `prompt`, `generated_text`, `created_at`, `application_id`.

## Client

`client/` is reserved for the React frontend (not yet built).
