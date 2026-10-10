# QA Test Plan — Sprint 3

Owner: Samad (QA Lead)
Scope: everything pushed to `main` as of commit `7845fa5` ("add student home
page with search, filters and time of day").
Test file: [`accounts/tests.py`](accounts/tests.py)

## How to run

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py test accounts
```

No `.env` or Google credentials are required — these tests create users
directly in the test database and never touch the real Google OAuth
handshake. 26 tests, all passing as of 2026-10-09.

## What's covered

### `User` model (`UserModelTests`)
- New users default to `role="student"`
- `role` choices (`student`/`moderator`) display correctly via `get_role_display()`

### Access control / routing (`AccessControlTests`)
- Logged-out requests to `/` and `/profile/` redirect to `/login/` (with `?next=`)
- Logged-in user hitting `/login/` redirects to `/` (home) — confirms the
  redirect target that changed in the latest commit (was `profile`, now `home`)
- Logged-in user can reach both `/` and `/profile/` (200 OK)

### Home page / shop list (`HomeViewShopListTests`)
- Default load returns all 4 shops, `time="now"`, `view="list"`
- Invalid `?time=` value falls back to `"now"` instead of erroring
- `?time=morning/afternoon/evening` changes displayed download/upload speeds
- `?q=` search is case-insensitive and filters by shop name
- No-match search shows the "No coffee shops match" empty state
- Each filter individually: Fast Wi-Fi, Outlets, Seating, Quiet, Open now
- Filters combined use AND logic
- `?view=map` shows the map placeholder instead of the shop list

### Role display / avatar (`HomeViewRoleAndAvatarTests`)
- Student vs. moderator role tag renders correctly
- Avatar initials built from first + last name
- Initials fall back to username when `first_name` is blank

### Profile page (`ProfileViewTests`)
- Shows the logged-in user's own name, email, and role

## Known issues found during QA (not fixed — reported to Sean, per team process: QA documents, doesn't patch)

1. **`SHOPS` global mutated in place per request** (`accounts/views.py`,
   `home()`). The module-level `SHOPS` list is shared across every request
   in the process; the view writes `shop["download"]`, `shop["upload"]`,
   `shop["label"]` directly onto those same dicts instead of copying them.
   Covered by `KnownBugRegressionTests.test_shops_global_is_mutated_in_place_by_request_handling`,
   which proves the shared dict keeps whichever request wrote to it last.
   This is a data-race risk if requests interleave (Django's dev server
   threads by default; a multi-threaded gunicorn config would too) — one
   user's selected time-of-day could leak into another user's response.
   **Fix needed:** build a new dict per shop per request instead of
   mutating `SHOPS`.

2. **No logout link on the home page.** `home.html` overrides
   `base.html`'s entire `{% block body %}`, so it never inherits the
   shared navbar (which has the Log out form). Since `/` is now the
   post-login landing page, there's currently no way to log out without
   first navigating to Profile. Covered by
   `KnownBugRegressionTests.test_home_page_has_no_logout_link`.

## Not covered (needs Sean's Google Cloud credentials)

- The real Google OAuth handshake (`/accounts/google/login/callback/`)
- Whether Sean's Cloud Console redirect URI is configured correctly
- Whether a given email is on the OAuth consent screen's test-user list

## Still missing from the sprint (no code to test yet)

- Admin home page (disputed ratings, Keep/Remove, starter ratings / Add rating)
- Profile page stats, badges, and "My recent tests" list from the wireframe
