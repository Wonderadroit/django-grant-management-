#!/bin/bash
# Production Monitoring Script for Django Grant Management System
# Run this script via cron every 5 minutes for continuous monitoring

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="/var/www/djf_grant_system"
LOG_FILE="/var/log/djf/monitoring.log"
ALERT_EMAIL="admin@davidjohnsonfoundation.org"
HEALTH_CHECK_URL="https://davidjohnsonfoundation.org/health/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Function to send alert email
send_alert() {
    local subject="$1"
    local message="$2"
    
    echo -e "Subject: $subject\n\n$message" | sendmail "$ALERT_EMAIL" 2>/dev/null || true
    log_message "ALERT: $subject - $message"
}

# Function to check service status
check_service() {
    local service_name="$1"
    
    if systemctl is-active --quiet "$service_name"; then
        log_message "INFO: $service_name is running"
        return 0
    else
        log_message "ERROR: $service_name is not running"
        send_alert "Service Down: $service_name" "$service_name service is not running on $(hostname)"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local threshold=85
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt "$threshold" ]; then
        log_message "WARNING: Disk usage is ${usage}% (threshold: ${threshold}%)"
        send_alert "High Disk Usage" "Disk usage is at ${usage}% on $(hostname)"
        return 1
    else
        log_message "INFO: Disk usage is ${usage}%"
        return 0
    fi
}

# Function to check memory usage
check_memory() {
    local threshold=90
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -gt "$threshold" ]; then
        log_message "WARNING: Memory usage is ${usage}% (threshold: ${threshold}%)"
        send_alert "High Memory Usage" "Memory usage is at ${usage}% on $(hostname)"
        return 1
    else
        log_message "INFO: Memory usage is ${usage}%"
        return 0
    fi
}

# Function to check database connectivity
check_database() {
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    if python manage.py dbshell --command="SELECT 1;" >/dev/null 2>&1; then
        log_message "INFO: Database connection successful"
        return 0
    else
        log_message "ERROR: Database connection failed"
        send_alert "Database Connection Failed" "Cannot connect to database on $(hostname)"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    if redis-cli ping >/dev/null 2>&1; then
        log_message "INFO: Redis connection successful"
        return 0
    else
        log_message "ERROR: Redis connection failed"
        send_alert "Redis Connection Failed" "Cannot connect to Redis on $(hostname)"
        return 1
    fi
}

# Function to check application health
check_application_health() {
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" --max-time 10)
    
    if [ "$response_code" = "200" ]; then
        log_message "INFO: Application health check passed (HTTP $response_code)"
        return 0
    else
        log_message "ERROR: Application health check failed (HTTP $response_code)"
        send_alert "Application Health Check Failed" "Health check returned HTTP $response_code on $(hostname)"
        return 1
    fi
}

# Function to check SSL certificate expiry
check_ssl_certificate() {
    local domain="davidjohnsonfoundation.org"
    local threshold_days=30
    
    local expiry_date=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    local expiry_epoch=$(date -d "$expiry_date" +%s)
    local current_epoch=$(date +%s)
    local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
    
    if [ "$days_until_expiry" -lt "$threshold_days" ]; then
        log_message "WARNING: SSL certificate expires in $days_until_expiry days"
        send_alert "SSL Certificate Expiring Soon" "SSL certificate for $domain expires in $days_until_expiry days"
        return 1
    else
        log_message "INFO: SSL certificate valid for $days_until_expiry days"
        return 0
    fi
}

# Function to check log file sizes
check_log_sizes() {
    local max_size_mb=100
    local log_dirs=("/var/log/djf" "/var/log/nginx")
    
    for log_dir in "${log_dirs[@]}"; do
        if [ -d "$log_dir" ]; then
            while IFS= read -r -d '' file; do
                local size_mb=$(du -m "$file" | cut -f1)
                if [ "$size_mb" -gt "$max_size_mb" ]; then
                    log_message "WARNING: Large log file: $file (${size_mb}MB)"
                    send_alert "Large Log File" "Log file $file is ${size_mb}MB on $(hostname)"
                fi
            done < <(find "$log_dir" -name "*.log" -type f -print0)
        fi
    done
}

# Function to check backup status
check_backup_status() {
    local backup_dir="/var/backups/djf"
    local max_age_hours=25  # Daily backups + 1 hour buffer
    
    if [ -d "$backup_dir" ]; then
        local latest_backup=$(find "$backup_dir" -name "full_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [ -n "$latest_backup" ]; then
            local backup_age_hours=$(( ($(date +%s) - $(stat -c %Y "$latest_backup")) / 3600 ))
            
            if [ "$backup_age_hours" -gt "$max_age_hours" ]; then
                log_message "WARNING: Latest backup is $backup_age_hours hours old"
                send_alert "Backup Outdated" "Latest backup is $backup_age_hours hours old on $(hostname)"
                return 1
            else
                log_message "INFO: Latest backup is $backup_age_hours hours old"
                return 0
            fi
        else
            log_message "ERROR: No backup files found"
            send_alert "No Backups Found" "No backup files found in $backup_dir on $(hostname)"
            return 1
        fi
    else
        log_message "ERROR: Backup directory not found"
        send_alert "Backup Directory Missing" "Backup directory $backup_dir not found on $(hostname)"
        return 1
    fi
}

# Function to check application metrics
check_application_metrics() {
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run Django health check command
    if python manage.py health_check --format=json > /tmp/health_check.json 2>&1; then
        local status=$(jq -r '.status' /tmp/health_check.json 2>/dev/null || echo "unknown")
        
        if [ "$status" = "healthy" ]; then
            log_message "INFO: Application metrics check passed"
            return 0
        else
            log_message "ERROR: Application metrics check failed - status: $status"
            local errors=$(jq -r '.checks | to_entries[] | select(.value.healthy == false) | .key' /tmp/health_check.json 2>/dev/null | tr '\n' ', ')
            send_alert "Application Metrics Failed" "Health check failed with errors: $errors on $(hostname)"
            return 1
        fi
    else
        log_message "ERROR: Could not run application health check"
        send_alert "Health Check Command Failed" "Unable to run Django health check on $(hostname)"
        return 1
    fi
}

# Main monitoring function
main() {
    log_message "=== Starting monitoring check ==="
    
    local check_results=()
    local all_passed=true
    
    # Run all checks
    checks=(
        "check_service nginx"
        "check_service postgresql"
        "check_service redis-server"
        "check_service djf-grant-system"
        "check_disk_space"
        "check_memory"
        "check_database"
        "check_redis"
        "check_application_health"
        "check_ssl_certificate"
        "check_log_sizes"
        "check_backup_status"
        "check_application_metrics"
    )
    
    for check in "${checks[@]}"; do
        if $check; then
            check_results+=("✅ $check")
        else
            check_results+=("❌ $check")
            all_passed=false
        fi
    done
    
    # Log summary
    log_message "=== Monitoring check summary ==="
    for result in "${check_results[@]}"; do
        log_message "$result"
    done
    
    if $all_passed; then
        log_message "INFO: All monitoring checks passed"
    else
        log_message "WARNING: Some monitoring checks failed"
    fi
    
    log_message "=== Monitoring check completed ==="
}

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Run monitoring if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi