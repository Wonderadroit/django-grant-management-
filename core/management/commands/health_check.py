"""
Production Health Check Command
Monitors system health and performance metrics
"""

from django.core.management.base import BaseCommand
from django.db import connections
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from grants.models import GrantApplication
import os
import psutil
import redis
import requests
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Comprehensive production health check'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='text',
            choices=['text', 'json'],
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.format = options['format']
        self.verbose = options['verbose']
        
        health_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }

        # Run all health checks
        checks = [
            ('database', self.check_database),
            ('cache', self.check_cache),
            ('disk_space', self.check_disk_space),
            ('memory', self.check_memory),
            ('cpu', self.check_cpu),
            ('services', self.check_services),
            ('application', self.check_application),
            ('security', self.check_security),
        ]

        for check_name, check_func in checks:
            try:
                result = check_func()
                health_data['checks'][check_name] = result
                
                if not result.get('healthy', True):
                    health_data['status'] = 'unhealthy'
                    
            except Exception as e:
                health_data['checks'][check_name] = {
                    'healthy': False,
                    'error': str(e),
                    'message': f'Health check failed: {str(e)}'
                }
                health_data['status'] = 'unhealthy'

        # Output results
        if self.format == 'json':
            import json
            self.stdout.write(json.dumps(health_data, indent=2))
        else:
            self.display_text_output(health_data)

        # Exit with non-zero code if unhealthy
        if health_data['status'] != 'healthy':
            exit(1)

    def check_database(self):
        """Check database connectivity and performance"""
        try:
            # Test database connection
            db_conn = connections['default']
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            # Check database size and statistics
            with db_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
                """)
                size, active_connections = cursor.fetchone()

            # Check recent applications
            recent_count = GrantApplication.objects.filter(
                created_at__gte=datetime.now() - timedelta(hours=24)
            ).count()

            return {
                'healthy': True,
                'database_size': size,
                'active_connections': active_connections,
                'recent_applications_24h': recent_count,
                'message': 'Database connection successful'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Database connection failed'
            }

    def check_cache(self):
        """Check Redis cache connectivity"""
        try:
            # Test cache connection
            cache.set('health_check', 'ok', 30)
            result = cache.get('health_check')
            
            if result != 'ok':
                raise Exception("Cache test failed")

            # Get Redis info
            redis_client = redis.Redis.from_url(settings.CACHES['default']['LOCATION'])
            redis_info = redis_client.info()

            return {
                'healthy': True,
                'redis_version': redis_info.get('redis_version'),
                'used_memory': redis_info.get('used_memory_human'),
                'connected_clients': redis_info.get('connected_clients'),
                'message': 'Cache connection successful'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Cache connection failed'
            }

    def check_disk_space(self):
        """Check disk space usage"""
        try:
            # Check root partition
            root_usage = psutil.disk_usage('/')
            
            # Check project directory
            project_usage = psutil.disk_usage(settings.BASE_DIR)
            
            # Calculate percentages
            root_percent = (root_usage.used / root_usage.total) * 100
            project_percent = (project_usage.used / project_usage.total) * 100
            
            # Alert if usage > 85%
            healthy = root_percent < 85 and project_percent < 85
            
            return {
                'healthy': healthy,
                'root_usage_percent': round(root_percent, 2),
                'project_usage_percent': round(project_percent, 2),
                'root_free_gb': round(root_usage.free / (1024**3), 2),
                'message': 'Disk space within acceptable limits' if healthy else 'Disk space running low'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Disk space check failed'
            }

    def check_memory(self):
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Alert if memory usage > 90%
            healthy = memory_percent < 90
            
            return {
                'healthy': healthy,
                'memory_usage_percent': memory_percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'message': 'Memory usage within acceptable limits' if healthy else 'High memory usage detected'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Memory check failed'
            }

    def check_cpu(self):
        """Check CPU usage"""
        try:
            # Get CPU usage over 1 second
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg()
            
            # Alert if CPU usage > 80%
            healthy = cpu_percent < 80
            
            return {
                'healthy': healthy,
                'cpu_usage_percent': cpu_percent,
                'load_average_1m': load_avg[0],
                'load_average_5m': load_avg[1],
                'load_average_15m': load_avg[2],
                'cpu_cores': psutil.cpu_count(),
                'message': 'CPU usage within acceptable limits' if healthy else 'High CPU usage detected'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'CPU check failed'
            }

    def check_services(self):
        """Check system services status"""
        try:
            services_to_check = ['nginx', 'postgresql', 'redis-server']
            service_status = {}
            all_healthy = True
            
            for service in services_to_check:
                try:
                    # Check if service is active
                    result = os.system(f'systemctl is-active --quiet {service}')
                    is_active = result == 0
                    service_status[service] = 'active' if is_active else 'inactive'
                    
                    if not is_active:
                        all_healthy = False
                        
                except Exception:
                    service_status[service] = 'unknown'
                    all_healthy = False

            return {
                'healthy': all_healthy,
                'services': service_status,
                'message': 'All services running' if all_healthy else 'Some services are down'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Service check failed'
            }

    def check_application(self):
        """Check application-specific metrics"""
        try:
            # Count applications by status
            status_counts = {}
            for status, _ in GrantApplication.STATUS_CHOICES:
                count = GrantApplication.objects.filter(status=status).count()
                status_counts[status] = count

            # Count users
            total_users = User.objects.count()
            active_users = User.objects.filter(last_login__gte=datetime.now() - timedelta(days=30)).count()

            # Check for pending applications
            pending_count = GrantApplication.objects.filter(status='submitted').count()

            return {
                'healthy': True,
                'total_applications': sum(status_counts.values()),
                'applications_by_status': status_counts,
                'total_users': total_users,
                'active_users_30d': active_users,
                'pending_applications': pending_count,
                'message': 'Application metrics collected'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Application check failed'
            }

    def check_security(self):
        """Check security-related metrics"""
        try:
            # Check for recent failed login attempts (if logging is set up)
            # Check SSL certificate expiry (basic check)
            # Check file permissions
            
            security_issues = []
            
            # Check .env file permissions
            env_file = os.path.join(settings.BASE_DIR, '.env')
            if os.path.exists(env_file):
                env_perms = oct(os.stat(env_file).st_mode)[-3:]
                if env_perms != '600':
                    security_issues.append(f'.env file permissions: {env_perms} (should be 600)')

            # Check DEBUG setting
            if getattr(settings, 'DEBUG', False):
                security_issues.append('DEBUG is enabled in production')

            # Check ALLOWED_HOSTS
            if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
                security_issues.append('ALLOWED_HOSTS not properly configured')

            healthy = len(security_issues) == 0

            return {
                'healthy': healthy,
                'security_issues': security_issues,
                'debug_enabled': getattr(settings, 'DEBUG', False),
                'allowed_hosts': settings.ALLOWED_HOSTS,
                'message': 'No security issues detected' if healthy else f'{len(security_issues)} security issues found'
            }

        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'message': 'Security check failed'
            }

    def display_text_output(self, health_data):
        """Display health check results in text format"""
        status_color = '\033[92m' if health_data['status'] == 'healthy' else '\033[91m'
        reset_color = '\033[0m'
        
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"🏥 PRODUCTION HEALTH CHECK - {health_data['timestamp']}")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Overall Status: {status_color}{health_data['status'].upper()}{reset_color}")
        self.stdout.write(f"{'='*60}\n")

        for check_name, check_data in health_data['checks'].items():
            status_icon = '✅' if check_data.get('healthy', True) else '❌'
            self.stdout.write(f"{status_icon} {check_name.upper().replace('_', ' ')}")
            self.stdout.write(f"   Message: {check_data.get('message', 'No message')}")
            
            if self.verbose:
                for key, value in check_data.items():
                    if key not in ['healthy', 'message', 'error']:
                        self.stdout.write(f"   {key}: {value}")
            
            if check_data.get('error'):
                self.stdout.write(f"   Error: {check_data['error']}")
            
            self.stdout.write("")

        self.stdout.write(f"{'='*60}")