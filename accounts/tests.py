"""
QA test suite for the accounts app (login, profile, home/shop list).

Covers everything pushed as of commit 7845fa5 ("add student home page with
search, filters and time of day"). These tests exercise the Django-side
logic only -- they create users directly instead of going through the real
Google OAuth handshake, so they do not require GOOGLE_CLIENT_ID/SECRET and
do not verify Sean's Google Cloud Console configuration (redirect URI,
test-user list, etc). See TESTING.md for what is and isn't covered here.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .views import SHOPS, speed_label

User = get_user_model()


class UserModelTests(TestCase):
    def test_new_user_defaults_to_student_role(self):
        user = User.objects.create_user(username="newstudent", password="x")
        self.assertEqual(user.role, "student")

    def test_role_choices_display_correctly(self):
        student = User.objects.create_user(username="s1", password="x", role="student")
        moderator = User.objects.create_user(username="m1", password="x", role="moderator")
        self.assertEqual(student.get_role_display(), "Student")
        self.assertEqual(moderator.get_role_display(), "Moderator")


class AccessControlTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viswa", password="x")

    def test_logged_out_home_redirects_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('home')}", fetch_redirect_response=False
        )

    def test_logged_out_profile_redirects_to_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('profile')}", fetch_redirect_response=False
        )

    def test_logged_in_user_hitting_login_redirects_to_home(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("login"))
        self.assertRedirects(response, reverse("home"))

    def test_logged_in_user_can_reach_home(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_logged_in_user_can_reach_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)


class HomeViewShopListTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viswa", password="x")
        self.client.force_login(self.user)

    def test_default_load_shows_all_shops(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(len(response.context["shops"]), len(SHOPS))
        self.assertEqual(response.context["time"], "now")
        self.assertEqual(response.context["view"], "list")

    def test_invalid_time_value_falls_back_to_now(self):
        response = self.client.get(reverse("home"), {"time": "nonsense"})
        self.assertEqual(response.context["time"], "now")

    def test_time_of_day_changes_displayed_speeds(self):
        # Values are copied out of the response immediately after each
        # request. Holding onto the dict objects themselves across both
        # requests would alias them together, since the view mutates the
        # shared SHOPS list in place rather than copying it (see
        # KnownBugRegressionTests.test_shops_global_is_mutated_in_place).
        morning = self.client.get(reverse("home"), {"time": "morning"})
        morning_download = next(
            s["download"] for s in morning.context["shops"] if s["name"] == "Grit (Corner)"
        )
        self.assertEqual(morning_download, 58)

        evening = self.client.get(reverse("home"), {"time": "evening"})
        evening_download = next(
            s["download"] for s in evening.context["shops"] if s["name"] == "Grit (Corner)"
        )
        self.assertEqual(evening_download, 44)

    def test_search_filters_by_name_case_insensitive(self):
        response = self.client.get(reverse("home"), {"q": "GRIT"})
        names = [s["name"] for s in response.context["shops"]]
        self.assertEqual(names, ["Grit (Corner)"])

    def test_search_with_no_match_returns_empty_list(self):
        response = self.client.get(reverse("home"), {"q": "nonexistent shop"})
        self.assertEqual(response.context["shops"], [])
        self.assertContains(response, "No coffee shops match")

    def test_fast_filter_keeps_only_fast_shops_for_selected_time(self):
        response = self.client.get(reverse("home"), {"fast": "1"})
        for shop in response.context["shops"]:
            self.assertEqual(speed_label(shop["download"]), "Fast")

    def test_outlets_filter_excludes_few_outlets(self):
        response = self.client.get(reverse("home"), {"outlets": "1"})
        names = [s["name"] for s in response.context["shops"]]
        self.assertNotIn("Bodo's (Corner)", names)
        self.assertNotIn("Starbucks (Corner)", names)

    def test_seating_filter_excludes_limited_seating(self):
        response = self.client.get(reverse("home"), {"seating": "1"})
        names = [s["name"] for s in response.context["shops"]]
        self.assertNotIn("Starbucks (Corner)", names)

    def test_quiet_filter_keeps_only_quiet_shops(self):
        response = self.client.get(reverse("home"), {"quiet": "1"})
        names = {s["name"] for s in response.context["shops"]}
        self.assertEqual(names, {"Grit (Corner)", "Starbucks (Corner)"})

    def test_open_filter_excludes_closed_shops(self):
        response = self.client.get(reverse("home"), {"open": "1"})
        names = [s["name"] for s in response.context["shops"]]
        self.assertNotIn("Bodo's (Corner)", names)

    def test_combined_filters_use_and_logic(self):
        response = self.client.get(reverse("home"), {"quiet": "1", "outlets": "1"})
        names = {s["name"] for s in response.context["shops"]}
        # quiet=1 allows Grit + Starbucks; outlets=1 then drops Starbucks (few outlets)
        self.assertEqual(names, {"Grit (Corner)"})

    def test_map_view_renders_placeholder_not_list(self):
        response = self.client.get(reverse("home"), {"view": "map"})
        self.assertContains(response, "Map view coming soon")
        self.assertNotContains(response, "shop-card")


class HomeViewRoleAndAvatarTests(TestCase):
    def test_student_sees_student_role_tag(self):
        user = User.objects.create_user(username="stu", password="x", role="student")
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertFalse(response.context["is_moderator"])
        self.assertContains(response, "Student")

    def test_moderator_sees_moderator_role_tag(self):
        user = User.objects.create_user(username="mod", password="x", role="moderator")
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertTrue(response.context["is_moderator"])
        self.assertContains(response, "Moderator")

    def test_initials_built_from_first_and_last_name(self):
        user = User.objects.create_user(
            username="viswa", password="x", first_name="Viswa", last_name="Subramanian"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["initials"], "VS")

    def test_initials_fall_back_to_username_when_first_name_blank(self):
        user = User.objects.create_user(username="noname", password="x", last_name="Smith")
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["first_name"], "noname")
        self.assertEqual(response.context["initials"], "NS")


class ProfileViewTests(TestCase):
    def test_profile_shows_logged_in_users_own_data(self):
        user = User.objects.create_user(
            username="viswa",
            password="x",
            email="sav4br@virginia.edu",
            first_name="Viswa",
            last_name="Subramanian",
            role="student",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.context["name"], "Viswa Subramanian")
        self.assertEqual(response.context["email"], "sav4br@virginia.edu")
        self.assertEqual(response.context["role"], "Student")


class BugFixRegressionTests(TestCase):
    """
    Regression tests for two bugs found during QA review and fixed on
    2026-10-10. See TESTING.md "Known Issues (fixed)" for details on each
    bug and the fix. These tests pin down the fixed behavior so a future
    change can't silently reintroduce either bug.
    """

    def test_shops_global_is_not_mutated_by_request_handling(self):
        """
        Was: accounts/views.py home() mutated the shared module-level
        SHOPS list directly (shop["download"] = ...) instead of building
        a copy, which was a data-race risk under concurrent requests --
        one user's request could leak into another's.
        Fix: the view now copies each shop dict (dict(original)) before
        writing computed fields onto it, so SHOPS itself is never changed.
        """
        grit_before = next(s for s in SHOPS if s["name"] == "Grit (Corner)")
        snapshot = dict(grit_before)

        user = User.objects.create_user(username="viswa", password="x")
        self.client.force_login(user)

        self.client.get(reverse("home"), {"time": "morning"})
        self.client.get(reverse("home"), {"time": "evening"})

        self.assertEqual(grit_before, snapshot, "SHOPS should be untouched by requests")
        self.assertNotIn("download", grit_before, "SHOPS entries should have no computed fields")

    def test_home_page_has_a_logout_control(self):
        """
        Was: home.html overrode base.html's entire `body` block, so it
        never inherited the shared navbar's Log out form. Home is the
        post-login landing page, so there was no way to log out from it
        without first clicking through to Profile.
        Fix: added a Log out form directly to home.html's bottom nav.
        """
        user = User.objects.create_user(username="viswa", password="x")
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, f'action="{reverse("account_logout")}"')
        self.assertContains(response, "Log out")

    def test_logout_from_home_page_actually_logs_out(self):
        user = User.objects.create_user(username="viswa", password="x")
        self.client.force_login(user)
        self.client.post(reverse("account_logout"))
        response = self.client.get(reverse("home"))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('home')}", fetch_redirect_response=False
        )
