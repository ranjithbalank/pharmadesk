"""SEC-3 / NFR-4: automatic local backup of the SQLite database.

Copies the live DB to a timestamped file under backend/backups/ (and, if
configured, to an off-machine path). Keeps the most recent N copies. Uses
SQLite's online backup API so it is safe to run while the app is in use.

Run daily via Task Scheduler, and on every app launch (see desktop.py).
Set an off-machine copy with the PHARMADESK_BACKUP_DIR env var (e.g. a
mapped drive or cloud-synced folder) to satisfy "a copy off the machine".
"""
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

KEEP = 14  # retain ~2 weeks of daily backups


class Command(BaseCommand):
    help = 'Back up the SQLite database to a timestamped local (and off-machine) copy.'

    def add_arguments(self, parser):
        parser.add_argument('--keep', type=int, default=KEEP,
                            help='Number of recent backups to retain locally.')

    def handle(self, *args, **options):
        db_path = Path(settings.DATABASES['default']['NAME'])
        if not db_path.exists():
            self.stdout.write(self.style.WARNING(f'No database at {db_path}; nothing to back up.'))
            return

        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        target = backup_dir / f'pharmadesk-{stamp}.sqlite3'

        self._sqlite_backup(db_path, target)
        self.stdout.write(self.style.SUCCESS(f'Local backup: {target}'))

        # Off-machine copy (external drive / cloud-synced folder).
        off = os.environ.get('PHARMADESK_BACKUP_DIR')
        if off:
            off_dir = Path(off)
            off_dir.mkdir(parents=True, exist_ok=True)
            off_target = off_dir / target.name
            shutil.copy2(target, off_target)
            self.stdout.write(self.style.SUCCESS(f'Off-machine copy: {off_target}'))
        else:
            self.stdout.write(self.style.WARNING(
                'No PHARMADESK_BACKUP_DIR set — local backup only. '
                'Set it to an external/cloud folder for off-machine safety (R-3).'
            ))

        self._prune(backup_dir, options['keep'])

    def _sqlite_backup(self, src: Path, dst: Path):
        """Consistent copy via SQLite's backup API (safe while in use)."""
        source = sqlite3.connect(str(src))
        dest = sqlite3.connect(str(dst))
        with dest:
            source.backup(dest)
        dest.close()
        source.close()

    def _prune(self, backup_dir: Path, keep: int):
        backups = sorted(backup_dir.glob('pharmadesk-*.sqlite3'), reverse=True)
        for old in backups[keep:]:
            old.unlink()
            self.stdout.write(f'Pruned old backup: {old.name}')
