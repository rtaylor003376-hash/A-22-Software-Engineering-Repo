# A-22 Wi-Fi Ratings

CS 3240 project. Right now this is just Google login and a profile page.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Put the Google client ID and secret in `.env`. The redirect URI to add in
Google Cloud Console is `http://localhost:8000/accounts/google/login/callback/`.

## User types

Everyone who logs in is a Student. To make someone a Moderator, change their
role in `/admin`.
