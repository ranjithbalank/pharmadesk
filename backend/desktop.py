"""PharmaDesk desktop launcher (BRD §9.4).

One process that: applies migrations, takes a startup backup, runs the Django
app on a local Waitress server, and opens it in a native desktop window
(pywebview). No internet required — everything is localhost.

    python desktop.py            # desktop window
    python desktop.py --browser  # serve only; open in your browser instead

Auto-start: register start-desktop.bat with Task Scheduler (see
install-autostart.ps1) so it launches at logon and the counter staff just
double-click one icon.
"""
import os
import sys
import threading
import time

# Packaged run: real server settings, UI served by Django (not Vite).
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_DEBUG'] = '0'

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

HOST, PORT = '127.0.0.1', 8000
URL = f'http://{HOST}:{PORT}/'


def prepare():
    """First-run/every-run setup: schema up to date, static present, safety backup."""
    call_command('migrate', interactive=False, verbosity=0)
    try:
        call_command('collectstatic', interactive=False, verbosity=0)
    except Exception as exc:  # non-fatal — UI may still be served from dist/
        print(f'collectstatic skipped: {exc}')
    try:
        call_command('backup_db')
    except Exception as exc:
        print(f'startup backup skipped: {exc}')


def serve():
    from waitress import serve as waitress_serve
    from config.wsgi import application
    waitress_serve(application, host=HOST, port=PORT, threads=8)


def main():
    prepare()
    threading.Thread(target=serve, daemon=True).start()

    # Give Waitress a moment to bind before pointing the window at it.
    time.sleep(1.0)

    if '--browser' in sys.argv:
        import webbrowser
        webbrowser.open(URL)
        print(f'PharmaDesk running at {URL} — press Ctrl+C to stop.')
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        return

    import webview
    webview.create_window(
        'PharmaDesk — Sri Sakthi Medicals', URL,
        width=1320, height=860, min_size=(1024, 680),
    )
    webview.start()


if __name__ == '__main__':
    main()
