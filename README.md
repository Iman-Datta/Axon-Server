<div align="center">

<br />

# AXON SERVER

**Git-aware Collaborative Project Management — Backend System**

<br />

![Status](https://img.shields.io/badge/Status-Under%20Active%20Development-orange?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.x-red?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Channels](https://img.shields.io/badge/Django%20Channels-WebSockets-4B8BBE?style=for-the-badge)


<br />

> Axon is a platform that bridges project management and version control.  
> Built for individual developers and teams who want their GitHub activity to drive their workflow automatically.

<br />

---

</div>

## Overview

Axon is a Git-aware collaborative project management system. Unlike traditional project management tools where developers must manually update task statuses, Axon integrates directly with GitHub repositories to reflect real development activity. Branch creation, commits, pull requests, and merges are automatically mapped to tickets, keeping the board in sync with the codebase without any manual overhead.

The system supports both personal and organization-level workspaces, structured role hierarchies, a Kanban-based ticket workflow, real-time notifications via WebSockets, and a complete audit trail of all project activity.

This repository contains the backend system only. The frontend client is maintained separately in `axon-client`.

---

## Features

| Area | Description |
|---|---|
| Authentication | JWT-based auth with secure token refresh |
| User Profiles | Independent profiles with GitHub username linking |
| Organizations | Team/company workspaces with org-level role hierarchy |
| Projects | Personal and organization-scoped projects |
| Memberships | Role-based access — Owner, Lead, Developer, Viewer |
| Groups | Member grouping — Frontend, Backend, DevOps, Design |
| Tickets | Full lifecycle ticketing with estimated time and countdown |
| Kanban Board | Todo → Development → Review → Done workflow |
| GitHub Integration | Webhook-driven automatic ticket status updates |
| Activity Logs | Immutable audit trail of all system events |
| Invitations | Invite users to projects or organizations with role assignment |
| Real-time | WebSocket-based live updates via Django Channels |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.x |
| API | Django REST Framework |
| Real-time | Django Channels (WebSockets) |
| Database | PostgreSQL 16 |
| Authentication | JWT (via djangorestframework-simplejwt) |
| Task Queue | Celery + Redis *(planned)* |
| GitHub Events | Webhooks (push, PR, merge) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
axon_backend/
│
├── config/                        # Project-level configuration
│   ├── settings/
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Development overrides
│   │   └── production.py          # Production overrides
│   ├── urls.py                    # Root URL configuration
│   ├── asgi.py                    # ASGI entry (Channels + HTTP)
│   └── wsgi.py
│
├── apps/
│   ├── core/                      # Shared utilities, base models, exceptions
│   ├── users/                     # User auth, profiles, JWT
│   ├── organizations/             # Organizations, org-level memberships
│   ├── projects/                  # Projects, GitHub repo linking
│   ├── members/                   # ProjectMember roles and groups
│   ├── tickets/                   # Tickets, Kanban status, countdown timer
│   ├── github_integration/        # Webhook receiver, event-to-ticket mapper
│   ├── activity/                  # ActivityLog — all system events
│   ├── invitations/               # Project and org invitation system
│   └── notifications/             # Real-time notification records
│
├── websockets/                    # Django Channels consumers and routing
│   ├── consumers.py
│   └── routing.py
│
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── manage.py
├── .env.example
└── docker-compose.yml
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (for Django Channels channel layer)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/axon-server.git
cd axon-server
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements/development.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root based on the provided example:

```bash
cp .env.example .env
```

Minimum required variables:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/axon_db
REDIS_URL=redis://localhost:6379/0
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
```

### 5. Apply Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

For WebSocket support, run via Daphne (ASGI):

```bash
daphne config.asgi:application
```

---

## GitHub Integration

Axon maps GitHub events to tickets using a naming convention in branch names and commit messages.

| Convention | Example |
|---|---|
| Branch name | `feature/ticket-101-login-page` |
| Commit message | `fix #101 resolve auth bug` |

| GitHub Event | Ticket Status Update |
|---|---|
| Branch created | Todo → Development |
| Commit pushed | Stays in Development |
| Pull request opened | Development → Review |
| PR merged | Review → Done |

Webhook endpoint: `POST /api/github/webhook/`

---

## API Overview

| Module | Base Endpoint |
|---|---|
| Authentication | `/api/auth/` |
| Users | `/api/users/` |
| Organizations | `/api/organizations/` |
| Projects | `/api/projects/` |
| Members | `/api/projects/{id}/members/` |
| Tickets | `/api/projects/{id}/tickets/` |
| Activity | `/api/projects/{id}/activity/` |
| Invitations | `/api/invitations/` |
| GitHub Webhook | `/api/github/webhook/` |

Full API documentation will be available via Swagger/Redoc at `/api/docs/` once the initial release is complete.

---

## Development Roadmap

- [x] Project architecture and database schema design
- [ ] User authentication system (JWT)
- [ ] Organization and project management
- [ ] Role-based access control
- [ ] Ticket and Kanban system
- [ ] GitHub webhook integration
- [ ] Activity logging
- [ ] Invitation system
- [ ] Real-time notifications (Django Channels)
- [ ] API documentation (Swagger)
- [ ] Dockerization
- [ ] Production deployment

---

## Contributing

This project is part of a final-year engineering project and is currently under active solo development. Contributions, suggestions, and feedback are welcome once the core system reaches a stable state.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">
<sub>Built with focus — Axon Server</sub>
</div>
