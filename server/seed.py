from app import app
from config import db
from models import Application, Response, User

SEED_PASSWORD = "password123"

SEED_DATA = {
    "demo": [
        {
            "company": "Stripe",
            "role": "Backend Engineer",
            "status": "interview",
            "job_description": (
                "Design and build reliable APIs for payment processing. "
                "Work with Python and Ruby services, own features end to end, "
                "and collaborate with product teams on high-scale systems."
            ),
            "response": {
                "prompt": "Tell us about a time you improved the reliability of a production system.",
                "generated_text": (
                    "On my last team, our order service dropped requests during traffic spikes. "
                    "I added request queuing and retry logic with exponential backoff, plus "
                    "alerting on queue depth. Failed requests fell by 90% and on-call pages "
                    "for that service dropped to near zero over the next quarter."
                ),
            },
        },
        {
            "company": "Airbnb",
            "role": "Full Stack Engineer",
            "status": "applied",
            "job_description": (
                "Build guest and host experiences across React and Java services. "
                "Ship polished UI, write clean APIs, and partner closely with design."
            ),
            "response": {
                "prompt": "Why do you want to work at Airbnb?",
                "generated_text": (
                    "I love products that connect people in the real world, and Airbnb does that "
                    "at a global scale. I'm excited by the chance to work across the stack, from "
                    "React interfaces to backend services, on features that help hosts and guests "
                    "trust each other."
                ),
            },
        },
        {
            "company": "Spotify",
            "role": "Data Engineer",
            "status": "rejected",
            "job_description": (
                "Build and maintain data pipelines that power listening insights and "
                "recommendations. Experience with SQL, Python, and distributed processing preferred."
            ),
        },
    ],
    "tester": [
        {
            "company": "Shopify",
            "role": "Software Developer",
            "status": "offer",
            "job_description": (
                "Help merchants succeed by building features in Ruby on Rails and React. "
                "Remote-friendly team focused on developer productivity and quality."
            ),
        },
        {
            "company": "Notion",
            "role": "Frontend Engineer",
            "status": "interview",
            "job_description": (
                "Craft fast, accessible editor experiences in TypeScript and React. "
                "Care deeply about performance and thoughtful interaction design."
            ),
        },
        {
            "company": "Datadog",
            "role": "Site Reliability Engineer",
            "status": "applied",
            "job_description": (
                "Keep large-scale monitoring infrastructure healthy. Work with Kubernetes, "
                "Terraform, and Go, and participate in an on-call rotation."
            ),
        },
    ],
}


def seed():
    print("Clearing existing data...")
    Response.query.delete()
    Application.query.delete()
    User.query.delete()

    print("Creating users, applications, and responses...")
    for username, applications in SEED_DATA.items():
        user = User(username=username)
        user.password_hash = SEED_PASSWORD
        db.session.add(user)

        for app_data in applications:
            application = Application(
                company=app_data["company"],
                role=app_data["role"],
                status=app_data["status"],
                job_description=app_data["job_description"],
                user=user,
            )
            if "response" in app_data:
                Response(**app_data["response"], application=application)
            db.session.add(application)

    db.session.commit()
    print(
        f"Done: {User.query.count()} users, {Application.query.count()} applications, "
        f"{Response.query.count()} responses."
    )


if __name__ == "__main__":
    with app.app_context():
        try:
            seed()
        except Exception:
            db.session.rollback()
            raise
