"""SEC-3: tested restore procedure. Restores the SQLite database from a
backup file produced by `backup_db`. Safeguards the current DB by copying
it aside first, so a mistaken restore is itself recoverable.

Usage:
    python manage.py restore_db                 # restore the latest backup
    python manage.py restore_db <path-to-file>  # restore a specific backup
"""
import shutil
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Restore the SQLite database from a backup (latest by default).'

    def add_arguments(self, parser):
        parser.add_argument('backup', nargs='?', help='Backup file to restore from.')
        parser.add_argument('--yes', action='store_true', help='Skip confirmation.')

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        backup_dir = settings.BASE_DIR / 'backups'

        if options['backup']:
            source = Path(options['backup'])
        else:
            backups = sorted(backup_dir.glob('pharmadesk-*.sqlite3'), reverse=True)
            if not backups:
                raise CommandError(f'No backups found in {backup_dir}.')
            source = backups[0]

        if not source.exists():
            raise CommandError(f'Backup file not found: {source}')

        if not options['yes']:
            self.stdout.write(self.style.WARNING(
                f'This will overwrite {db_path}\n  with {source}\n'
                'Stop the app first. Re-run with --yes to proceed.'
            ))
            return

        # Park the current DB so this restore is itself reversible.
        if db_path.exists():
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            parked = db_path.with_name(f'db.before-restore-{stamp}.sqlite3')
            shutil.copy2(db_path, parked)
            self.stdout.write(f'Current DB parked at: {parked}')

        shutil.copy2(source, db_path)
        self.stdout.write(self.style.SUCCESS(f'Restored database from {source}.'))
