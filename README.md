# [Django Boilerplate](https://www.youtube.com/watch?v=bGGDGltRT_g)

**Open-Source Web App** coded in **Django Framework** on top of **Argon Dashboard** design. **Features**:

- SQLite, Django native ORM
- Modular design
- Session-Based authentication (login, register)
- Forms validation
- UI Kit: **Argon Dashboard** provided by **Creative-Tim**

<br />

![Django Boilerplate - Open-Source Web App.](https://raw.githubusercontent.com/app-generator/static/master/products/django-boilerplate-intro.gif)

<br />

## How to use it

```bash
$ # Get the code
$ git clone https://github.com/app-generator/django-boilerplate.git
$ cd django-boilerplate
$
$ # Virtualenv modules installation (Unix based systems)
$ virtualenv --no-site-packages env
$ source env/bin/activate
$
$ # Virtualenv modules installation (Windows based systems)
$ # virtualenv --no-site-packages env
$ # .\env\Scripts\activate
$ 
$ # Install modules
$ # SQLIte version
$ pip3 install -r requirements.txt
$
$ # Create tables
$ python manage.py makemigrations
$ python manage.py migrate
$
$ # Start the application (development mode)
$ python manage.py runserver
$
$ # Access the web app in browser: http://127.0.0.1:8000/
```

<br />

## Docker execution

@WIP

<br />

## Credits & Links

- [Django Boilerplate](https://www.youtube.com/watch?v=bGGDGltRT_g) - yTube presentation
- [Django Framework](https://www.djangoproject.com/) - Offcial website

<br />

## License

@MIT

<br />

## Developer notes

- Fix migrated placeholder emails: `python manage.py fix_grant_emails`
- Development email backend prints emails to the console (see `core/settings.py`).
- Admin actions for `GrantApplication` allow marking approved/rejected and will send emails (console backend in dev).

## Deployment & Security (recommendations)

- Keep `SECRET_KEY` out of source control. Use environment variables or a secrets manager and set `SECRET_KEY` in your environment (see `.env.example`).
- Set `DEBUG=False` in production and add your domain(s) to `ALLOWED_HOSTS`.
- Use HTTPS in production. Enable `SECURE_SSL_REDIRECT`, set `SESSION_COOKIE_SECURE=True`, and `CSRF_COOKIE_SECURE=True`.
- Configure a proper email backend for production (SMTP, SendGrid, etc.).
- Use a production-ready server (Gunicorn / Daphne) behind a reverse proxy (Nginx).
- Regularly run security checks: `python manage.py check --deploy` and fix any issues.


---
[Django Boilerplate](https://www.youtube.com/watch?v=bGGDGltRT_g) - provided by **AppSeed**
