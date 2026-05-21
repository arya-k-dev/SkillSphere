# SkillSphere

SkillSphere is a peer-to-peer skill exchange platform built with Django. It helps people teach what they know, learn what they want, and grow through reciprocal learning instead of monetary transactions.

The platform connects learners and mentors through skill profiles, intelligent match recommendations, exchange requests, scheduled sessions, feedback, achievements, certificates, messaging, and dashboard analytics.

## Project Overview

SkillSphere is designed around mutual learning. A user can list skills they can teach and skills they want to learn, then the system recommends compatible peers based on overlapping skill titles, categories, levels, location, and activity. Once a request is accepted, the platform creates an active exchange with chat, sessions, ratings, achievements, and certificate flows.

## Key Features

| Area | Implemented Features |
| --- | --- |
| Authentication | User signup, login, logout, Django auth integration, automatic profile creation |
| Onboarding | Multi-step onboarding for profile details and teach/learn skills |
| Profiles | Profile viewing and editing with name, headline, bio, location, availability, learning goal, and role |
| Skills | Add, edit, delete, browse, and view teach/learn skills with category, level, mode, and description |
| Matching | Recommended matches, match scoring, match details, exchange request sending, acceptance, decline, and cancellation |
| Exchanges | Accepted requests create `SkillExchange` records and activate communication between users |
| Sessions | Schedule, edit, cancel, complete, and review learning sessions |
| Ratings | Session feedback with 1-5 star ratings, comments, and tags |
| Certificates | Automatic certificate generation for completed exchanges with enough feedback |
| Achievements | Badge-style achievement tracking, progress, unlocks, leaderboard, and community pages |
| Dashboard | Modern dashboard with metrics, recommendations, activity, progress cards, upcoming sessions, and Chart.js analytics |
| Notifications | Notification model, unread counts, notification page, mark-read, read-all, and clear-read flows |
| Messaging | Inbox and exchange-based chat threads after accepted requests |
| Admin | Django admin is enabled for managing registered project models |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Django 6.0.5 |
| Database | SQLite (`db.sqlite3`) |
| Frontend | HTML, CSS, JavaScript |
| UI Assets | Custom CSS, SVG logo/favicon, PNG hero/auth images |
| Charts | Chart.js via CDN on the dashboard |
| Icons | Font Awesome via CDN in the dashboard base template |
| Images | Pillow 12.2.0 |
| Static Files | Django staticfiles |

Tailwind CSS is not currently installed or referenced in the project. The UI is implemented with custom CSS in `static/css/style.css`.

## Project Structure

```text
SKILLSPHERE2/
├── accounts/              # Authentication, registration, onboarding, profiles
├── core/                  # Home page, dashboard, public exploration redirects, search
├── skills/                # Skill CRUD, public browse/detail pages
├── matching/              # Match scoring, recommendations, requests, exchanges
├── messaging/             # Chat threads, messages, notifications
├── notifications/         # Notification context processor package
├── sessions/              # Skill exchange sessions and feedback
├── engagement/            # Achievements, certificates, leaderboard, community
├── skillsphere/           # Django project settings, URL config, ASGI/WSGI
├── templates/             # Shared base templates
├── static/                # Source CSS, JavaScript, images
├── staticfiles/           # Collected static output
├── db.sqlite3             # Local SQLite database
├── manage.py              # Django management entry point
└── requirements.txt       # Python dependencies
```

Notes:

- No custom `admin_dashboard` app is present; administration uses Django's built-in `/admin/`.
- No `media/` directory is currently present.
- Ratings and certificates are implemented through the `sessions` and `engagement` apps rather than separate `ratings` or `certificates` apps.

## Application Modules

| App | Purpose |
| --- | --- |
| `accounts` | Handles registration, login/logout templates, profile management, onboarding profile form, onboarding skill formsets, and profile auto-creation signals. |
| `core` | Provides the landing page, dashboard analytics, global search, public skill exploration redirects, and demo data seeding command. |
| `skills` | Manages skill listings for teaching and learning, including public browse/detail pages and authenticated CRUD views. |
| `matching` | Calculates recommended matches, manages match request lifecycle, prevents duplicate active requests, and creates skill exchanges. |
| `messaging` | Creates chat threads for accepted exchanges, stores messages, and manages notifications. |
| `sessions` | Schedules and tracks exchange sessions, completion details, attendance, hours, resources, assignments, and feedback. |
| `engagement` | Tracks achievements, user badge progress, certificates, leaderboard scoring, and community metrics. |
| `notifications` | Supplies notification context data to templates. |

## UI / Design System

SkillSphere uses a custom soft-modern visual system with:

- Green/teal brand palette and clean white surfaces
- Glassmorphism-style cards and subtle shadows
- Responsive dashboard shell with sidebar navigation
- Rounded cards, pills, badges, status labels, and progress indicators
- Hover states, scroll reveal effects, animated counters, and hero parallax
- Chart.js dashboard visualizations
- Shared public and dashboard layouts through `templates/base.html` and `templates/dashboard_base.html`

Primary UI files:

- `static/css/style.css`
- `static/js/animations.js`
- `templates/base.html`
- `templates/dashboard_base.html`

## Database Models

| Model | App | Purpose |
| --- | --- | --- |
| `Profile` | `accounts` | Extends Django users with full name, headline, bio, location, availability, learning goal, role, and onboarding state. |
| `Skill` | `skills` | Stores teach/learn skills with category, description, level, mode, owner, and timestamps. |
| `MatchRequest` | `matching` | Represents an exchange request between users, including offered/requested skills, message, score, and status. |
| `SkillExchange` | `matching` | Represents an accepted skill exchange between two users. |
| `ChatThread` | `messaging` | One chat thread per accepted skill exchange. |
| `Message` | `messaging` | Individual chat messages with sender, body, read state, and timestamp. |
| `Notification` | `messaging` | User notifications for requests, messages, sessions, ratings, badges, and certificates. |
| `Session` | `sessions` | Scheduled learning session with mentor, learner, date/time, format, status, completion notes, attendance, and hours. |
| `SessionFeedback` | `sessions` | Participant feedback for a session, including rating, comments, and tags. |
| `Achievement` | `engagement` | Badge definition with code, name, description, points, target value, and icon label. |
| `UserAchievement` | `engagement` | Tracks unlocked achievements and progress for a user. |
| `Certificate` | `engagement` | Certificate records for learner completion or mentor contribution. |

## Main Routes

| URL | App | Description |
| --- | --- | --- |
| `/` | `core` | Landing page |
| `/dashboard/` | `core` | Authenticated dashboard |
| `/search/` | `core` | Global search |
| `/accounts/register/` | `accounts` | Signup |
| `/accounts/login/` | `accounts` | Login |
| `/accounts/logout/` | `accounts` | Logout |
| `/accounts/onboarding/profile/` | `accounts` | Onboarding profile step |
| `/accounts/onboarding/skills/` | `accounts` | Onboarding skills step |
| `/accounts/profile/` | `accounts` | Profile view |
| `/accounts/profile/edit/` | `accounts` | Profile edit |
| `/skills/` | `skills` | Skill list |
| `/skills/browse/` | `skills` | Public skill browse |
| `/skills/add/` | `skills` | Add skill |
| `/skills/my/` | `skills` | My skills |
| `/matching/` | `matching` | Recommended matches |
| `/matching/requests/` | `matching` | Match requests |
| `/matching/exchanges/` | `matching` | Active exchanges |
| `/messages/` | `messaging` | Inbox |
| `/messages/exchange/<exchange_id>/` | `messaging` | Exchange chat |
| `/sessions/` | `sessions` | Sessions list |
| `/sessions/schedule/<exchange_id>/` | `sessions` | Schedule session |
| `/ratings/` | `sessions` | Ratings page |
| `/achievements/` | `engagement` | Achievements |
| `/certificates/` | `engagement` | Certificates |
| `/leaderboard/` | `engagement` | Leaderboard |
| `/community/` | `engagement` | Community page |
| `/notifications/` | `messaging` | Notifications |
| `/admin/` | Django admin | Admin interface |

## Installation Guide

1. Clone the project:

```bash
git clone <repository-url>
cd SKILLSPHERE2
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows Command Prompt
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Create a superuser:

```bash
python manage.py createsuperuser
```

7. Optional: seed demo data:

```bash
python manage.py seed_demo_data
```

8. Run the development server:

```bash
python manage.py runserver
```

## How to Run

Start the Django development server:

```bash
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Environment Setup

The current project uses direct settings in `skillsphere/settings.py` and does not currently load a `.env` file.

For production, move sensitive values into environment variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- Database credentials if switching from SQLite

## Management Commands

| Command | Purpose |
| --- | --- |
| `python manage.py seed_demo_data` | Seeds demo users, skills, exchanges, sessions, achievements, and certificates. |
| `python manage.py send_session_reminders` | Sends session reminder notifications for upcoming sessions. |
| `python manage.py dedupe_match_requests` | Cleans duplicate match requests. |

## Screenshots

Add screenshots to a future `docs/screenshots/` folder or embed them here.

| Page | Screenshot |
| --- | --- |
| Home page | `docs/screenshots/home.png` |
| Dashboard | `docs/screenshots/dashboard.png` |
| Matches | `docs/screenshots/matches.png` |
| Skills | `docs/screenshots/skills.png` |
| Certificates | `docs/screenshots/certificates.png` |
| Achievements | `docs/screenshots/achievements.png` |

## Future Enhancements

- AI-powered skill recommendations and personalized learning paths
- Real-time chat with WebSockets
- Built-in video sessions and calendar integrations
- Stronger gamification with streaks, quests, and seasonal challenges
- Skill verification, endorsements, and mentor credibility signals
- Community groups, forums, events, and peer circles
- Public certificate verification page by verification code
- Production-ready environment configuration and deployment pipeline

## Contributors

| Name | Role |
| --- | --- |
| Add contributor name | Project owner / developer |

## License

This project is intended for educational and portfolio use. Add a formal license file before public distribution.
