# Django Grant Management

A focused Django backend for managing grant opportunities and applicant submissions.

## What it demonstrates

- Django project structure and configuration
- Relational domain modelling with `Grant` and `Application`
- Django admin integration
- A small JSON API for open grants
- Automated tests
- Database migrations
- GitHub Actions CI across supported Python versions

## Architecture

```text
Django project
├── grant_management/   # settings, URLs, WSGI entry point
└── grants/             # domain models, API view, admin, tests
```

### Core domain

- **Grant** — a funding opportunity with description, deadline and open/closed state.
- **Application** — an applicant submission linked to a grant with an explicit workflow status.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver
```

On Windows, activate the environment with `.venv\\Scripts\\activate`.

The grant listing endpoint is available at `/api/grants/` when the development server is running.

## CI

GitHub Actions runs the Django test suite on Python **3.11, 3.12 and 3.13** and checks that migrations are in sync. This follows the standard GitHub Actions model of building/testing changes automatically on repository events. citeturn0search3

## Security notes

- Do not commit real secrets or production credentials.
- The development `SECRET_KEY` in source is intentionally non-production and must be replaced through environment configuration before deployment.
- `DEBUG` must be disabled in production.
- Authentication/authorization for applicant and administrative workflows is a planned production concern and is not claimed to be complete yet.

## Status

**Working portfolio implementation — not production-ready.**

The current release establishes the domain model, API boundary, migrations, admin integration and automated test baseline. Future work should add authentication/authorization, validation rules, applicant-facing forms, production configuration, stronger security controls and deployment documentation.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the implementation roadmap.

## License

No license is currently specified.

---

**Author:** [Wonderadroit](https://github.com/Wonderadroit)
