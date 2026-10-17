# ApplyTrack

ApplyTrack is a full-stack job application tracker. Users log the jobs they apply to, track each application's status from applied to offer, and generate AI-drafted answers to screening questions with Google Gemini. Drafts are tailored to the application's company, role, and job description, and every generated response is saved with its application so good answers can be reused later.

## Features

- Sign up, log in, and stay logged in across page refreshes (JWT authentication)
- Create, view, edit, and delete job applications with company, role, status, and job description
- Dashboard of application cards with color-coded status badges and a count of applications by status
- Change an application's status directly from its detail page
- Generate a first-person draft answer to a screening question using Google Gemini, tailored to the application
- Drafts use bracketed placeholders like `[your experience with X]` instead of inventing experience
- Saved responses are listed newest first, with copy-to-clipboard and delete
- Failed AI requests show a clear error and a Retry button, and nothing is saved
- Mock AI mode for developing and demoing without an API key
- Each user can only see and change their own data

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, React Router 7, Vite 8, plain CSS |
| Backend | Python 3.12, Flask, Flask-CORS |
| Database | SQLite with Flask-SQLAlchemy and Flask-Migrate (Alembic) |
| Auth | Flask-JWT-Extended (JWT access tokens), Flask-Bcrypt (password hashing) |
| AI | Google Gemini via the `google-genai` Python SDK |
| Config | python-dotenv, pipenv |

## Data Models

| Model | Key fields | Relationships |
|---|---|---|
| **User** (`users`) | `id`, `username` (unique, required), `_password_hash` (bcrypt, never returned by the API) | Has many Applications (deleting a user deletes their applications) |
| **Application** (`applications`) | `id`, `company` (required), `role` (required), `status` (`applied`, `interview`, `offer`, or `rejected`; defaults to `applied`), `job_description`, `user_id` | Belongs to a User; has many Responses (deleting an application deletes its responses) |
| **Response** (`responses`) | `id`, `prompt` (the screening question), `generated_text` (the AI draft), `created_at`, `application_id` | Belongs to an Application |

## API Routes

All routes return JSON. Protected routes need an `Authorization: Bearer <token>` header. In development the React app calls these through the Vite proxy at `/api` (for example `/api/login`), and the proxy forwards them to Flask without the `/api` prefix.

| Method | Route | Token | Purpose |
|---|---|---|---|
| GET | `/` | No | Health check: `{"message": "ApplyTrack API running"}` |
| POST | `/signup` | No | Create an account (`username`, `password` of 8+ characters). Returns the user and a token |
| POST | `/login` | No | Log in. Returns the user and a token |
| GET | `/me` | Yes | Get the logged-in user |
| GET | `/applications` | Yes | List the user's applications, newest first |
| POST | `/applications` | Yes | Create an application |
| GET | `/applications/<id>` | Yes | Get one application with its saved responses |
| PATCH | `/applications/<id>` | Yes | Update `company`, `role`, `status`, and/or `job_description` |
| DELETE | `/applications/<id>` | Yes | Delete an application and its responses |
| GET | `/applications/<id>/responses` | Yes | List an application's saved responses, newest first |
| POST | `/applications/<id>/responses` | Yes | Generate an AI draft for `{"question": "..."}` (5 to 1000 characters) and save it |
| DELETE | `/responses/<id>` | Yes | Delete a saved response |

Tokens expire after 24 hours.

## Setup

### Prerequisites

- Python 3.12
- [pipenv](https://pipenv.pypa.io/) (`pip install --user pipenv`)
- Node.js 20.19 or newer (or 22.12+), with npm

### 1. Clone the repo

```bash
git clone https://github.com/donotfalter-lab/ApplyTrack.git
cd ApplyTrack
```

### 2. Backend

```bash
cd server
pipenv install
cp .env.example .env
```

Open `server/.env` and set `JWT_SECRET_KEY` to a random value. You can generate one with:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

`.env.example` starts with `AI_MOCK=true`, so the app works without a Gemini key. See [Environment Variables](#environment-variables) to turn on real AI responses.

Create the database, load the demo data, and start the server:

```bash
pipenv run flask db upgrade
pipenv run python seed.py
pipenv run flask run --port 5555
```

The API is now running at http://localhost:5555. Leave this terminal open.

### 3. Frontend

In a second terminal, from the repo root:

```bash
cd client
npm install
npm run dev
```

### 4. Open the app

Go to **http://localhost:5173** in your browser and log in with the [demo account](#demo-login).

If port 5173 is already in use, Vite picks the next free port (such as 5174) and prints the address to open as the "Local:" URL in the terminal.

## Environment Variables

These go in `server/.env`, which is git-ignored. `server/.env.example` is a template you can copy.

| Variable | What it does | Example |
|---|---|---|
| `JWT_SECRET_KEY` | Secret used to sign login tokens. Required. | `replace-with-a-long-random-string` |
| `GEMINI_API_KEY` | Your Google Gemini API key. If blank, the app uses mock AI responses. | `your-gemini-api-key` |
| `GEMINI_MODEL` | Gemini model used for drafts. Defaults to `gemini-3.8-flash` if blank. | `gemini-3.8-flash` |
| `AI_MOCK` | `true` returns sample drafts without calling Gemini. `false` uses the real API. | `true` |

**Getting a free Gemini API key:** sign in at [aistudio.google.com](https://aistudio.google.com) with a Google account, choose **Get API key**, and create a key. Paste it into `GEMINI_API_KEY` and set `AI_MOCK=false`. The free tier has per-minute and daily limits.

**Running without a key:** with `AI_MOCK=true` (or no `GEMINI_API_KEY`), generating a response returns a realistic sample draft that uses the application's company and role. It is saved like a real response, so every feature works without an API key or quota.

Restart the Flask server after changing `.env`.

> **Note:** `pipenv run` loads `.env` itself and overrides variables set on the command line. To change a setting, edit `.env` rather than prefixing the command.

## Demo Login

`seed.py` creates two users, each with three applications. Demo has two saved responses.

| Username | Password |
|---|---|
| `demo` | `password123` |
| `tester` | `password123` |

Run `pipenv run python seed.py` from `server/` at any time to reset the data.

## Error Handling

Every error from the API is JSON in the form `{"error": "message"}`, and the React app shows that message to the user.

- **Validation errors (400):** missing or empty company or role, an invalid status, a password under 8 characters, a question outside 5 to 1000 characters, or a request body that isn't JSON. The frontend also checks required fields, password length and match, and question length before sending. Any failed database write is rolled back.
- **Duplicate username (409):** signing up with a taken username.
- **Wrong login (401):** the same "Invalid username or password" message whether the username or the password is wrong.
- **Missing, invalid, or expired token (401):** the API returns a JSON error. The frontend clears the saved token and sends the user to the login page.
- **Records that don't exist or belong to another user (404):** both return the same "Not found" response, so no one can tell whether another user's record exists. The frontend shows a "not found" page with a link back to the dashboard.
- **Failed AI requests:** timeouts (504), rate limits or used-up quota (429), and other Gemini problems such as an invalid key, an unavailable model, a blocked or empty answer, or a service outage (502) return a plain-language message. **Nothing is saved** to the database. The question stays in the text box and a **Retry** button resends it.
- **Backend not running:** the frontend shows "Can't reach the server. Is the backend running?"

## Screenshots

_Screenshots coming soon. I'll add the images to a `screenshots/` folder._

![Dashboard](screenshots/dashboard.png)

![Application detail](screenshots/application-detail.png)

![Response generator](screenshots/response-generator.png)

## Future Improvements

- Search and filtering on the dashboard
- Status analytics, such as charts of applications over time and by status
- Resume upload to personalize AI responses
- PostgreSQL and production deployment

## Author

**JaMyll Herbert**
GitHub: [github.com/donotfalter-lab](https://github.com/donotfalter-lab)
