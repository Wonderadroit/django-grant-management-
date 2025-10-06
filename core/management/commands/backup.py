"""
Production Backup Management Command
Handles database backups, media file backups, and cleanup
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import os
import subprocess
import gzip
import shutil
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage production backups (database, media files, logs)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='full',
            choices=['database', 'media', 'logs', 'full'],
            help='Type of backup to perform (default: full)'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old backups (keeps last 7 days)'
        )
        parser.add_argument(
            '--restore',
            type=str,
            help='Restore from backup file path'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List available backups'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        cleanup = options['cleanup']
        restore_file = options['restore']
        list_backups = options['list']

        # Set up backup directory
        self.backup_dir = getattr(settings, 'BACKUP_STORAGE_PATH', '/var/backups/djf/')
        os.makedirs(self.backup_dir, exist_ok=True)

        # Handle different operations
        if list_backups:
            self.list_available_backups()
        elif restore_file:
            self.restore_backup(restore_file)
        elif cleanup:
            self.cleanup_old_backups()
        else:
            self.create_backup(backup_type)

    def create_backup(self, backup_type):
        """Create backups based on type"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(f"🔄 Starting {backup_type} backup at {timestamp}")
        
        if backup_type in ['database', 'full']:
            self.backup_database(timestamp)
        
        if backup_type in ['media', 'full']:
            self.backup_media_files(timestamp)
        
        if backup_type in ['logs', 'full']:
            self.backup_logs(timestamp)
        
        if backup_type == 'full':
            self.create_full_backup_archive(timestamp)
        
        self.stdout.write(self.style.SUCCESS(f"✅ {backup_type.title()} backup completed successfully"))

    def backup_database(self, timestamp):
        """Backup PostgreSQL database"""
        try:
            self.stdout.write("📦 Backing up database...")
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '5432')
            
            # Create backup filename
            backup_filename = f"database_backup_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            compressed_path = f"{backup_path}.gz"
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            # Run pg_dump
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '--verbose',
                '--no-password',
                '--clean',
                '--create',
                '-f', backup_path
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            # Compress the backup
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(backup_path)
            
            # Get file size
            file_size = os.path.getsize(compressed_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(f"   ✅ Database backup saved: {compressed_path} ({size_mb:.2f} MB)")
            
            return compressed_path
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Database backup failed: {str(e)}"))
            logger.error(f"Database backup failed: {str(e)}")
            return None

    def backup_media_files(self, timestamp):
        """Backup media files"""
        try:
            self.stdout.write("📁 Backing up media files...")
            
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                self.stdout.write("   ⚠️  Media directory doesn't exist, skipping...")
                return None
            
            # Create backup filename
            backup_filename = f"media_backup_{timestamp}.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create tar.gz archive
            cmd = ['tar', '-czf', backup_path, '-C', os.path.dirname(media_root), 
                   os.path.basename(media_root)]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar command failed: {result.stderr}")
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(f"   ✅ Media backup saved: {backup_path} ({size_mb:.2f} MB)")
            
            return backup_path
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Media backup failed: {str(e)}"))
            logger.error(f"Media backup failed: {str(e)}")
            return None

    def backup_logs(self, timestamp):
        """Backup log files"""
        try:
            self.stdout.write("📋 Backing up log files...")
            
            log_dirs = [
                '/var/log/djf/',
                '/var/log/nginx/',
                os.path.join(settings.BASE_DIR, 'logs/')
            ]
            
            # Find existing log directories
            existing_dirs = [d for d in log_dirs if os.path.exists(d)]
            
            if not existing_dirs:
                self.stdout.write("   ⚠️  No log directories found, skipping...")
                return None
            
            # Create backup filename
            backup_filename = f"logs_backup_{timestamp}.tar.gz"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create tar.gz archive with all log directories
            cmd = ['tar', '-czf', backup_path] + existing_dirs
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar command failed: {result.stderr}")
            
            # Get file size
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(f"   ✅ Logs backup saved: {backup_path} ({size_mb:.2f} MB)")
            
            return backup_path
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Logs backup failed: {str(e)}"))
            logger.error(f"Logs backup failed: {str(e)}")
            return None

    def create_full_backup_archive(self, timestamp):
        """Create a combined archive of all backups"""
        try:
            self.stdout.write("📦 Creating full backup archive...")
            
            # Find all backup files for this timestamp
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if timestamp in filename and not filename.endswith('_full.tar.gz'):
                    backup_files.append(os.path.join(self.backup_dir, filename))
            
            if not backup_files:
                self.stdout.write("   ⚠️  No individual backups found for archiving")
                return None
            
            # Create full backup filename
            full_backup_filename = f"full_backup_{timestamp}.tar.gz"
            full_backup_path = os.path.join(self.backup_dir, full_backup_filename)
            
            # Create manifest file
            manifest_filename = f"manifest_{timestamp}.txt"
            manifest_path = os.path.join(self.backup_dir, manifest_filename)
            
            with open(manifest_path, 'w') as f:
                f.write(f"Full Backup Created: {datetime.now().isoformat()}\n")
                f.write(f"Django Version: {settings.DEBUG}\n")
                f.write(f"Backup Contents:\n")
                for backup_file in backup_files:
                    file_size = os.path.getsize(backup_file)
                    f.write(f"  - {os.path.basename(backup_file)} ({file_size} bytes)\n")
            
            # Add manifest to backup files
            backup_files.append(manifest_path)
            
            # Create combined archive
            cmd = ['tar', '-czf', full_backup_path, '-C', self.backup_dir] + \
                  [os.path.basename(f) for f in backup_files]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar command failed: {result.stderr}")
            
            # Get file size
            file_size = os.path.getsize(full_backup_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(f"   ✅ Full backup archive: {full_backup_path} ({size_mb:.2f} MB)")
            
            # Clean up individual backup files
            for backup_file in backup_files:
                if backup_file != manifest_path:  # Keep manifest
                    os.remove(backup_file)
            
            return full_backup_path
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Full backup archive failed: {str(e)}"))
            logger.error(f"Full backup archive failed: {str(e)}")
            return None

    def cleanup_old_backups(self):
        """Clean up backups older than 7 days"""
        try:
            self.stdout.write("🧹 Cleaning up old backups...")
            
            cutoff_date = datetime.now() - timedelta(days=7)
            removed_count = 0
            total_size_removed = 0
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_modified < cutoff_date:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        removed_count += 1
                        total_size_removed += file_size
                        self.stdout.write(f"   🗑️  Removed: {filename}")
            
            size_mb = total_size_removed / (1024 * 1024)
            self.stdout.write(f"   ✅ Cleanup completed: {removed_count} files removed ({size_mb:.2f} MB freed)")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Cleanup failed: {str(e)}"))
            logger.error(f"Backup cleanup failed: {str(e)}")

    def list_available_backups(self):
        """List all available backup files"""
        self.stdout.write("📋 Available Backups:")
        self.stdout.write("=" * 80)
        
        if not os.path.exists(self.backup_dir):
            self.stdout.write("No backup directory found.")
            return
        
        backup_files = []
        for filename in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                backup_files.append((filename, file_size, file_modified))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[2], reverse=True)
        
        if not backup_files:
            self.stdout.write("No backup files found.")
            return
        
        for filename, file_size, file_modified in backup_files:
            size_mb = file_size / (1024 * 1024)
            age = datetime.now() - file_modified
            age_str = f"{age.days}d {age.seconds//3600}h ago"
            
            backup_type = "🗄️  Full" if "full_backup" in filename else \
                         "💾 Database" if "database_backup" in filename else \
                         "📁 Media" if "media_backup" in filename else \
                         "📋 Logs" if "logs_backup" in filename else "❓ Unknown"
            
            self.stdout.write(f"{backup_type:<12} {filename:<40} {size_mb:>8.2f} MB  {age_str}")

    def restore_backup(self, restore_file):
        """Restore from a backup file"""
        self.stdout.write(f"🔄 Restoring from backup: {restore_file}")
        
        if not os.path.exists(restore_file):
            self.stdout.write(self.style.ERROR(f"Backup file not found: {restore_file}"))
            return
        
        # Determine backup type from filename
        if "database_backup" in os.path.basename(restore_file):
            self.restore_database(restore_file)
        elif "full_backup" in os.path.basename(restore_file):
            self.restore_full_backup(restore_file)
        else:
            self.stdout.write(self.style.ERROR("Unknown backup type. Cannot restore."))

    def restore_database(self, backup_file):
        """Restore database from backup"""
        try:
            self.stdout.write("🔄 Restoring database...")
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            db_name = db_settings['NAME']
            db_user = db_settings['USER']
            db_host = db_settings.get('HOST', 'localhost')
            db_port = db_settings.get('PORT', '5432')
            
            # Decompress if needed
            if backup_file.endswith('.gz'):
                temp_file = backup_file[:-3]  # Remove .gz extension
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                sql_file = temp_file
                cleanup_temp = True
            else:
                sql_file = backup_file
                cleanup_temp = False
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings['PASSWORD']
            
            # Restore database
            cmd = [
                'psql',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-f', sql_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
            # Clean up temporary file
            if cleanup_temp:
                os.remove(sql_file)
            
            self.stdout.write("   ✅ Database restored successfully")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Database restore failed: {str(e)}"))
            logger.error(f"Database restore failed: {str(e)}")

    def restore_full_backup(self, backup_file):
        """Restore from full backup archive"""
        try:
            self.stdout.write("🔄 Extracting full backup...")
            
            # Create temporary extraction directory
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract archive
            cmd = ['tar', '-xzf', backup_file, '-C', temp_dir]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"tar extraction failed: {result.stderr}")
            
            # Find and restore database backup
            for filename in os.listdir(temp_dir):
                if "database_backup" in filename:
                    db_backup_path = os.path.join(temp_dir, filename)
                    self.restore_database(db_backup_path)
                    break
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            self.stdout.write("   ✅ Full backup restored successfully")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Full backup restore failed: {str(e)}"))
            logger.error(f"Full backup restore failed: {str(e)}")
            
            # Clean up on error
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)