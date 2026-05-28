# SkillSphere Project Documentation

This document describes the technical structure of the SkillSphere Django project as implemented in the current codebase.

## 1. Architecture Summary

SkillSphere is a monolithic Django application organized into focused apps. It uses Django templates for server-rendered pages, custom CSS and JavaScript for UI behavior, SQLite for local development storage, and Django's built-in authentication and admin systems.

```text
Browser
  |
  | HTTP requests
  v
Django URL router
  |
  | includes app-level URL modules
  v
Views and forms
  |
  | query/update
  v
Models and SQLite database
  |
  | render
  v
Templates + static CSS/JS/images
```

## 2. Installed Apps

The active apps are declared in `skillsphere/settings.py`:

| App | Installed As | Responsibility |
| --- | --- | --- |
| `core` | `core` | Landing page, dashboard, search, public skill exploration redirects |
| `accounts` | `accounts` | Registration, profiles, onboarding, auth templates |
| `skills` | `skills` | Skill CRUD and public skill browsing |
| `matching` | `matching` | Match recommendations, requests, accepted exchanges |
| `messaging` | `messaging` | Chat threads, chat messages, notifications |
| `engagement` | `engagement.apps.EngagementConfig` | Certificates, leaderboard, community |
| `sessions` | `sessions.apps.SkillSessionsConfig` | Session scheduling, completion, ratings |
| Django contrib apps | `admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles` | Framework services |

The `notifications` package is present and provides context processor support, but notification persistence is implemented in `messaging.models.Notification`.

## 3. Settings and Runtime Configuration

Important settings:

| Setting | Current Value / Behavior |
| --- | --- |
| `ROOT_URLCONF` | `skillsphere.urls` |
| `DATABASES.default` | SQLite database at `BASE_DIR / "db.sqlite3"` |
| `STATIC_URL` | `static/` |
| `STATIC_ROOT` | `BASE_DIR / "staticfiles"` |
| `STATICFILES_DIRS` | `BASE_DIR / "static"` |
| `LOGIN_URL` | `accounts:login` |
| `LOGIN_REDIRECT_URL` | `core:dashboard` |
| `LOGOUT_REDIRECT_URL` | `core:home` |
| Template dirs | Root `templates/` plus app templates |
| Context processors | Django defaults plus `notifications.context_processors.notification_context` |

There is no `.env` loader currently configured. Sensitive production settings should be moved out of `settings.py` before deployment.

## 4. URL Architecture

Root URL configuration is in `skillsphere/urls.py`.

| Prefix | Included Module / View | Purpose |
| --- | --- | --- |
| `/admin/` | Django admin | Built-in admin dashboard |
| `/` | `core.urls` | Home, dashboard, search, exploration |
| `/accounts/` | `accounts.urls` | Auth, registration, onboarding, profile |
| `/skills/` | `skills.urls` | Skill pages |
| `/matching/` | `matching.urls` | Matching and exchange request pages |
| `/messages/` | `messaging.urls` | Inbox and chat |
| `/sessions/` | `sessions.urls` | Session management |
| `/` | `engagement.urls` | Certificates, leaderboard, community |
| `/ratings/` | `sessions.views.ratings_page` | Ratings page |
| `/notifications/` | `messaging.views.notification_list` | Notifications |
| `/requests/` | `matching.views.*` aliases | Request list and request actions |

## 5. Route Inventory

### Core

| Route | View | Notes |
| --- | --- | --- |
| `/` | `home` | Public landing page with stats and learner stories |
| `/explore/` | `explore_skills` | Redirects to skill browse |
| `/explore/<slug>/` | `explore_skill_detail` | Authenticated redirect to public skill detail |
| `/search/` | `global_search` | Authenticated global search |
| `/dashboard/` | `dashboard` | Authenticated analytics dashboard |

### Accounts

| Route | View | Notes |
| --- | --- | --- |
| `/accounts/register/` | `register` | Creates user, profile, and starts onboarding |
| `/accounts/login/` | Django `LoginView` | Uses `accounts/login.html` |
| `/accounts/logout/` | Django `LogoutView` | Redirects home |
| `/accounts/onboarding/profile/` | `onboarding_profile` | Collects profile details |
| `/accounts/onboarding/skills/` | `onboarding_skills` | Collects teach and learn skills |
| `/accounts/profile/` | `profile_view` | Authenticated profile view |
| `/accounts/profile/edit/` | `profile_edit` | Authenticated profile edit |

### Skills

| Route | View | Notes |
| --- | --- | --- |
| `/skills/` | `skill_list` | Authenticated skill list |
| `/skills/browse/` | `public_skill_browse` | Public category-style skill browsing |
| `/skills/add/` | `skill_add` | Add skill |
| `/skills/my/` | `my_skills` | User-owned skill listings |
| `/skills/<int:pk>/` | `skill_detail` | Skill detail |
| `/skills/<int:pk>/edit/` | `skill_edit` | Edit skill |
| `/skills/<int:pk>/delete/` | `skill_delete` | Delete skill |
| `/skills/<slug:slug>/` | `public_skill_detail` | Public skill category detail |

### Matching

| Route | View | Notes |
| --- | --- | --- |
| `/matching/` | `recommended_matches` | Ranked peer recommendations |
| `/matching/user/<user_id>/` | `match_detail` | Match profile and skill fit |
| `/matching/request/<user_id>/send/` | `send_match_request` | Send exchange request |
| `/matching/requests/` | `match_requests` | Sent and received requests |
| `/matching/exchanges/` | `my_exchanges` | Accepted exchanges |
| `/matching/request/<request_id>/accept/` | `accept_match_request` | Accept request and create exchange |
| `/matching/request/<request_id>/decline/` | `decline_match_request` | Decline request |
| `/matching/request/<request_id>/cancel/` | `cancel_match_request` | Cancel sent request |

The project also defines alias routes under `/requests/` and `/matching/requests/...`.

### Messaging and Notifications

| Route | View | Notes |
| --- | --- | --- |
| `/messages/` | `messages_inbox` | Exchange chat inbox |
| `/messages/exchange/<exchange_id>/` | `exchange_chat` | Chat for accepted exchange |
| `/notifications/` | `notification_list` | Notification list |
| `/notifications/<notification_id>/read/` | `mark_notification_read` | Mark one as read |
| `/notifications/read-all/` | `mark_all_notifications_read` | Mark all as read |
| `/notifications/clear-read/` | `clear_read_notifications` | Delete read notifications |

### Sessions and Ratings

| Route | View | Notes |
| --- | --- | --- |
| `/sessions/` | `sessions_list` | User sessions |
| `/sessions/schedule/<exchange_id>/` | `schedule_session` | Schedule session for accepted exchange |
| `/sessions/<session_id>/` | `session_detail` | Session detail |
| `/sessions/<session_id>/edit/` | `edit_session` | Edit session |
| `/sessions/<session_id>/cancel/` | `cancel_session` | Cancel session |
| `/sessions/<session_id>/complete/` | `mark_session_complete` | Mark complete and capture notes |
| `/sessions/<session_id>/feedback/` | `submit_session_feedback` | Submit rating and feedback |
| `/ratings/` | `ratings_page` | Ratings overview |

### Engagement

| Route | View | Notes |
| --- | --- | --- |
| `/certificates/` | `certificates_page` | User certificates |
| `/certificates/<certificate_id>/` | `certificate_detail` | Certificate detail |
| `/leaderboard/` | `leaderboard_page` | Ranked community users |
| `/community/` | `community_page` | Community metrics page |

## 6. Data Model Details

### `accounts.Profile`

One-to-one extension of Django's `User`.

Important fields:

- `full_name`
- `headline`
- `bio`
- `location`
- `availability`
- `learning_goal`
- `role`: learner, teacher, or both
- `is_onboarding_completed`

`accounts.signals.create_user_profile` creates a profile automatically when a user is created.

### `skills.Skill`

Represents a skill owned by a user.

Important fields:

- `user`
- `title`
- `category`
- `description`
- `skill_type`: teach or learn
- `level`: beginner, intermediate, advanced
- `mode`: online, offline, hybrid

### `matching.MatchRequest`

Represents an exchange request from one user to another.

Important fields:

- `sender`
- `receiver`
- `offered_skill`
- `requested_skill`
- `message`
- `status`: pending, accepted, declined, cancelled
- `score`

Important behavior:

- Prevents users from sending requests to themselves.
- Prevents duplicate pending or accepted active requests for the same skill pair.
- `accept(user)` creates or links a `SkillExchange`.
- Accepting a request calls `ensure_exchange_communication()` to create chat and acceptance notification.

### `matching.SkillExchange`

Represents an accepted exchange between two users.

Important fields:

- `request`
- `requester`
- `responder`
- `offered_skill`
- `requested_skill`

This model anchors chat threads, sessions, certificates, and exchange history.

### `messaging.ChatThread`

Represents a chat channel for one accepted exchange.

Important fields:

- `exchange`
- `user_one`
- `user_two`
- `is_active`

Useful methods:

- `get_partner(user)`
- `includes_user(user)`
- `get_absolute_url()`
- `unread_count_for(user)`

### `messaging.Message`

Stores chat messages.

Important fields:

- `thread`
- `sender`
- `body`
- `is_read`
- `created_at`

### `messaging.Notification`

Stores user-facing notifications.

Notification types:

- request sent
- request accepted
- request rejected
- message
- session
- rating
- badge
- certificate

### `sessions.Session`

Represents a learning session between the users in a skill exchange.

Important fields:

- `exchange`
- `request`
- `mentor`
- `learner`
- `title`
- `description`
- `scheduled_date`
- `scheduled_time`
- `duration_minutes`
- `format`: video call, chat, in person
- `location`
- `meeting_link`
- `status`: scheduled, in progress, completed, cancelled
- `topics_covered`
- `shared_resources`
- `assignments`
- `mentor_attendance`
- `learner_attendance`
- `hours_taught`
- `hours_learned`
- `completed_at`
- reminder flags

Important behavior:

- Validates that mentor and learner are different.
- Validates that scheduled sessions are not in the past.
- Validates that mentor and learner belong to the exchange.

### `sessions.SessionFeedback`

Stores session ratings and comments.

Important fields:

- `session`
- `given_by`
- `rating`
- `comments`
- `tags`

Important behavior:

- Rating must be between 1 and 5.
- Only session participants can submit feedback.
- One feedback record per user per session.

### `engagement.Certificate`

Represents learner completion or mentor contribution certificates.

Important fields:

- `certificate_id`
- `user`
- `skill`
- `exchange`
- `session`
- `certificate_type`
- `title`
- `mentor_name`
- `learner_name`
- `rating`
- `hours_completed`
- `sessions_count`
- `verification_code`
- `issued_date`

Certificate IDs and verification codes are generated automatically.

## 7. Matching Algorithm

Matching logic lives in `matching/utils.py`.

Main functions:

- `get_recommended_matches(current_user)`
- `build_match_data(current_user, other_user)`
- `calculate_match_score(current_user, other_user)`
- `get_exchange_skill_pair(current_user, other_user)`
- `get_match_request_state(...)`

Scoring inputs:

| Signal | Score Contribution |
| --- | --- |
| Other user teaches what current user wants to learn | +50 |
| Current user teaches what other user wants to learn | +30 |
| Shared skill category | +10 |
| Matching skill level | +5 |
| Same listed location | +5 |

Scores are capped at 100 and labeled as:

- Excellent Match: 80+
- Strong Match: 60+
- Good Match: 40+
- Basic Match: below 40

## 8. Feature Flows

### Registration and Onboarding

1. User registers at `/accounts/register/`.
2. A `Profile` is created through the accounts signal.
3. User is redirected to onboarding profile.
4. User adds profile details.
5. User adds skills they can teach and skills they want to learn.
6. Onboarding is marked complete.
7. User lands on the dashboard.

### Skill Exchange Flow

1. User creates teach and learn skills.
2. User opens recommended matches.
3. Matching utilities score compatible users.
4. User views a match detail page.
5. User sends a `MatchRequest`.
6. Receiver accepts, declines, or ignores the request.
7. Accepted request creates a `SkillExchange`.
8. Messaging service creates a `ChatThread`.
9. Users schedule sessions for the exchange.
10. Completed sessions collect hours, notes, resources, and assignments.
11. Participants submit feedback.
12. Certificates are evaluated from completed work.

### Messaging Flow

1. A match request is accepted.
2. `ensure_exchange_communication()` creates or activates the exchange chat thread.
3. Users open `/messages/` or the exchange chat route.
4. Sending a message creates a `Message`.
5. The recipient receives a `Notification`.

### Certificate Flow

1. A user completes sessions in an exchange.
2. The exchange has completed sessions with enough feedback.
3. `ensure_certificates_for_user(user)` determines learner or mentor certificate type.
4. A `Certificate` is created with generated IDs and verification code.

## 9. Templates

### Shared Templates

| Template | Purpose |
| --- | --- |
| `templates/base.html` | Public site layout, navbar, footer, static CSS/JS |
| `templates/dashboard_base.html` | Authenticated dashboard shell, sidebar, topbar, notification UI |

### App Templates

| App | Templates |
| --- | --- |
| `accounts` | login, register, onboarding profile, onboarding skills, profile view, profile form |
| `core` | home, dashboard, search results |
| `skills` | skill list, my skills, skill form, skill detail, skill card, public browse, public detail, delete confirmation |
| `matching` | recommended matches, match card, match detail, match requests, my exchanges |
| `messaging` | inbox, chat, notifications |
| `sessions` | sessions list, session card, schedule, detail, complete, feedback form/display, ratings |
| `engagement` | certificates, certificate detail, leaderboard, community |

## 10. Static Assets

Source static files live in `static/`.

| Path | Purpose |
| --- | --- |
| `static/css/style.css` | Main design system, layouts, responsive rules, dashboard styling |
| `static/js/animations.js` | Scroll reveal, counters, landing hero parallax |
| `static/images/skillsphere-exchange-logo-v2.svg` | Logo |
| `static/images/skillsphere-favicon-v2.svg` | Favicon |
| `static/images/skillsphere-homepage-skill-exchange-hero.png` | Homepage hero image |
| `static/images/skillsphere-login-collaboration.png` | Login page image |
| `static/images/skillsphere-signup-peer-learning.png` | Signup/register image |

`staticfiles/` is the collected static output directory.

## 11. Forms

| Form | App | Purpose |
| --- | --- | --- |
| `RegistrationForm` | `accounts` | User signup fields |
| `ProfileForm` | `accounts` | Profile editing |
| `OnboardingProfileForm` | `accounts` | Onboarding profile details |
| `OnboardingSkillForm` | `accounts` | Onboarding teach/learn skill rows |
| `SkillForm` | `skills` | Skill create/edit |
| `MatchRequestForm` | `matching` | Exchange request message |
| `SessionScheduleForm` | `sessions` | Session scheduling |
| `SessionEditForm` | `sessions` | Session editing |
| `SessionCompleteForm` | `sessions` | Session completion notes and attendance |
| `SessionFeedbackForm` | `sessions` | Ratings and feedback |

## 12. Admin Registration

The project uses Django admin at `/admin/`. Admin classes are present for the key models:

- `ProfileAdmin`
- `SkillAdmin`
- `MatchRequestAdmin`
- `SkillExchangeAdmin`
- `ChatThreadAdmin`
- `MessageAdmin`
- `NotificationAdmin`
- `SessionAdmin`
- `SessionFeedbackAdmin`
- `CertificateAdmin`

## 13. Context Processors

Configured context processor:

- `notifications.context_processors.notification_context`

Related messaging context utilities:

- `messaging.context_processors.notification_counts`

These support notification badges, unread counts, and dashboard/topbar notification UI.

## 14. Management Commands

| Command | File | Purpose |
| --- | --- | --- |
| `seed_demo_data` | `core/management/commands/seed_demo_data.py` | Creates demo platform data |
| `send_session_reminders` | `sessions/management/commands/send_session_reminders.py` | Creates session reminder notifications |
| `dedupe_match_requests` | `matching/management/commands/dedupe_match_requests.py` | Removes duplicate match request records |

## 15. Current Limitations and Notes

- The project uses SQLite and `DEBUG = True`, which is suitable for local development only.
- No `.env` support is currently configured.
- No custom `admin_dashboard` app exists; admin functionality uses Django admin.
- No `media/` directory or user-upload handling is currently configured.
- Messaging is request/response based; real-time WebSocket chat is not implemented yet.
- Tailwind CSS is not installed; the UI is custom CSS.

## 16. Suggested Production Checklist

- Move secrets and environment-specific values to environment variables.
- Set `DEBUG = False`.
- Configure `ALLOWED_HOSTS`.
- Use PostgreSQL or another production database.
- Configure static file hosting.
- Add media storage if profile images or uploads are introduced.
- Add automated tests for matching, request lifecycle, sessions, and certificates.
- Add CI checks for migrations and Django system checks.
- Add a formal license file.
