#!/bin/bash

# Ubuntu Systemd Deployment Script for Danloo Services
# This script starts and enables all Danloo systemd services

set -e

echo "🚀 Starting Danloo systemd services deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Check if environment file exists
if [ ! -f "/opt/danloo/.env" ]; then
    print_error "Environment file /opt/danloo/.env not found"
    print_error "Please create it from /opt/danloo/.env.example"
    exit 1
fi

# Create log directory and files with correct permissions
print_status "Creating log directory and files..."
mkdir -p /var/log/danloo
touch /var/log/danloo/{frontend,frontend-error,backend,admin,ai-provider,ai-proxy,process,nginx,nginx-minio}.log
chown -R danloo:danloo /var/log/danloo
chmod 755 /var/log/danloo
chmod 644 /var/log/danloo/*.log

# Set up logrotate configuration
print_status "Setting up logrotate configuration..."
cp /opt/danloo/systemdfiles/danloo-logrotate /etc/logrotate.d/danloo
chmod 644 /etc/logrotate.d/danloo

# Sync Python dependencies using uv workspace
print_status "Syncing Python dependencies..."
cd /opt/danloo
/usr/local/bin/uv sync

# Reload systemd daemon to pick up new service files
print_status "Reloading systemd daemon..."
systemctl daemon-reload

# List of services to start (in dependency order)
services=(
    "danloo-frontend"
    "danloo-nginx"
    "danloo-nginx-minio"
    "danloo-admin"
    "danloo-ai-provider"
    "danloo-ai-proxy"
    "danloo-backend"
    "danloo-process"
)

# Start services in order
print_status "Starting Danloo services..."
for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service.service"; then
        print_status "Starting $service..."
        systemctl start "$service"

        # Check if service started successfully
        if systemctl is-active --quiet "$service"; then
            print_status "✓ $service started successfully"
        else
            print_error "✗ $service failed to start"
            print_error "Check logs with: journalctl -u $service -f"
        fi
    else
        print_warning "Service $service not found, skipping..."
    fi
done

# Enable services for auto-start on boot
print_status "Enabling services for auto-start on boot..."
for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service.service"; then
        systemctl enable "$service"
        print_status "✓ $service enabled for auto-start"
    fi
done

# Show status of all services
print_status "Service status summary:"
echo "================================"
for service in "${services[@]}"; do
    if systemctl list-unit-files | grep -q "$service.service"; then
        if systemctl is-active --quiet "$service"; then
            echo -e "${GREEN}✓ $service: RUNNING${NC}"
        else
            echo -e "${RED}✗ $service: FAILED${NC}"
        fi
    else
        echo -e "${YELLOW}? $service: NOT FOUND${NC}"
    fi
done
echo "================================"

# Show helpful commands
print_status "Deployment completed!"
echo ""
print_status "Useful commands:"
echo "  View all service status: systemctl status danloo-*"
echo "  View service logs: journalctl -u danloo-frontend -f"
echo "  Stop all services: systemctl stop danloo-frontend danloo-backend danloo-ai-provider danloo-process danloo-ai-proxy danloo-admin danloo-nginx danloo-nginx-minio"
echo "  Restart a service: systemctl restart danloo-frontend"
echo ""
print_status "Access points:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  Admin: http://localhost:8003"
echo "  Nginx proxy: http://localhost:80"
echo "  MinIO proxy: http://localhost:9000"
echo ""
print_status "Log management:"
echo "  Log directory: /var/log/danloo/"
echo "  Logrotate configured: Daily rotation, 500MB max per service, 30 days retention"
echo "  View service logs: tail -f /var/log/danloo/<service>.log"
echo "  Manual logrotate: logrotate -f /etc/logrotate.d/danloo"
