# QA Test Plan — Sprint 3

Owner: Samad (QA Lead)
Scope: everything pushed to `main` as of commit `7845fa5` ("add student home
page with search, filters and time of day"), plus two bug fixes applied
directly by QA on 2026-10-10 (see "Known issues (fixed)" below).
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
handshake. 27 tests, all passing as of 2026-10-10.

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

## Known issues (fixed by QA on 2026-10-10)

Both bugs below were found during QA review of commit `7845fa5` and fixed
directly, with regression tests added in `BugFixRegressionTests` so neither
can silently come back. Sean was notified of both before the fix was made.

1. **`SHOPS` global mutated in place per request** (`accounts/views.py`,
   `home()`). The module-level `SHOPS` list is shared across every request
   in the process; the view wrote `shop["download"]`, `shop["upload"]`,
   `shop["label"]` directly onto those same dicts instead of copying them.
   This was a data-race risk if requests interleave (Django's dev server
   threads by default; a multi-threaded gunicorn config would too) — one
   user's selected time-of-day could leak into another user's response.

   **Fix:** the loop now does `shop = dict(original)` to copy each shop
   before writing the computed `download`/`upload`/`label` fields onto it,
   so `SHOPS` itself is never mutated. See `accounts/views.py` in the
   `home()` view.

   **Test:** `BugFixRegressionTests.test_shops_global_is_not_mutated_by_request_handling`
   snapshots a shop before two requests with different `time` values and
   asserts `SHOPS` is byte-for-byte unchanged afterward.

2. **No logout link on the home page.** `home.html` overrides
   `base.html`'s entire `{% block body %}`, so it never inherited the
   shared navbar (which has the Log out form). Since `/` is the
   post-login landing page, there was no way to log out from it without
   first navigating to Profile.

   **Fix:** added a `Log out` form (POST to `account_logout`, with CSRF
   token) directly into `home.html`'s existing bottom nav, alongside
   Home/Speed test/Profile. It sits outside the page's `<form method="get">`
   search/filter form so it isn't nested inside it (nested `<form>`
   elements are invalid HTML). Matching CSS (`.bottom-nav form`,
   `.bottom-nav button`) was added to `accounts/static/style.css` so the
   button looks like the other bottom-nav items instead of a default
   browser button.

   **Test:** `BugFixRegressionTests.test_home_page_has_a_logout_control`
   checks the form is rendered; `test_logout_from_home_page_actually_logs_out`
   posts to it and confirms the session is actually cleared (home then
   redirects to login).

## Not covered (needs Sean's Google Cloud credentials)

- The real Google OAuth handshake (`/accounts/google/login/callback/`)
- Whether Sean's Cloud Console redirect URI is configured correctly
- Whether a given email is on the OAuth consent screen's test-user list

## Still missing from the sprint (no code to test yet)

- Admin home page (disputed ratings, Keep/Remove, starter ratings / Add rating)
- Profile page stats, badges, and "My recent tests" list from the wireframe
