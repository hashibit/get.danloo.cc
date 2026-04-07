#!/bin/bash

# Ubuntu Initialization Script for Danloo Systemd Deployment
# This script prepares an Ubuntu system for deploying Danloo services via systemd

set -e

echo "🚀 Starting Ubuntu system initialization for Danloo systemd deployment..."

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

# Update system
print_status "Updating system packages..."
apt-get update
apt-get upgrade -y

# Function to check and install packages if needed
install_packages_if_needed() {
    local packages=("$@")
    local missing_packages=()

    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_status "Installing missing packages: ${missing_packages[*]}"
        apt-get install -y "${missing_packages[@]}"
    else
        print_status "All basic utilities are already installed"
    fi
}

# Install basic utilities
print_status "Checking basic utilities..."
basic_packages=(
    curl wget git htop vim nano tree net-tools
    supervisor logrotate fail2ban ufw
)
install_packages_if_needed "${basic_packages[@]}"

# Install Nginx if not already installed
if ! dpkg -l | grep -q "^ii  nginx "; then
    print_status "Installing Nginx..."
    apt-get install -y nginx
else
    print_status "Nginx is already installed"
fi

# Stop and disable system nginx to avoid port conflicts with danloo-nginx
print_status "Stopping and disabling system nginx service..."
if systemctl is-active --quiet nginx; then
    systemctl stop nginx
    print_status "Stopped system nginx service"
fi
if systemctl is-enabled --quiet nginx; then
    systemctl disable nginx
    print_status "Disabled system nginx service"
fi

# Install Node.js 20.x if not already installed (LTS until 2026-04)
if ! command -v node &> /dev/null; then
    print_status "Installing Node.js 20.x LTS..."
    # 下载安装脚本并验证后执行，避免直接管道执行
    NODEJS_SETUP="/tmp/nodejs_setup_20.x.sh"
    curl -fsSL https://deb.nodesource.com/setup_20.x -o "$NODEJS_SETUP"
    # 检查文件是否下载成功且非空
    if [ ! -s "$NODEJS_SETUP" ]; then
        print_error "Failed to download Node.js setup script"
        exit 1
    fi
    bash "$NODEJS_SETUP"
    rm -f "$NODEJS_SETUP"
    apt-get install -y nodejs
else
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        print_warning "Node.js version is $NODE_VERSION, recommend upgrading to 20.x"
    else
        print_status "Node.js $(node -v) is already installed"
    fi
fi

# Install Python and related packages if needed
print_status "Checking Python installation..."
python_packages=(python3 python3-pip python3-venv python3-dev build-essential)
install_packages_if_needed "${python_packages[@]}"

# Install MySQL development packages for mysqlclient
print_status "Installing MySQL development packages..."
mysql_packages=(default-libmysqlclient-dev pkg-config)
install_packages_if_needed "${mysql_packages[@]}"

# Install uv (Python package manager) if not already installed
if ! command -v uv &> /dev/null; then
    print_status "Installing uv (Python package manager)..."
    # 下载安装脚本并验证后执行，避免直接管道执行
    UV_INSTALL_SCRIPT="/tmp/uv_install.sh"
    curl -LsSf https://astral.sh/uv/install.sh -o "$UV_INSTALL_SCRIPT"
    # 检查文件是否下载成功且非空
    if [ ! -s "$UV_INSTALL_SCRIPT" ]; then
        print_error "Failed to download uv install script"
        exit 1
    fi
    # 执行安装脚本
    sh "$UV_INSTALL_SCRIPT"
    rm -f "$UV_INSTALL_SCRIPT"
    # Copy uv binaries to system-wide location
    if [ -f "$HOME/.local/bin/uv" ]; then
        cp "$HOME/.local/bin/uv" /usr/local/bin/
        cp "$HOME/.local/bin/uvx" /usr/local/bin/
        print_status "uv installed to /usr/local/bin"
    else
        print_error "uv installation failed - cannot find uv binary"
        exit 1
    fi
else
    print_status "uv $(uv --version 2>/dev/null || echo '') is already installed"
fi

# Install global npm packages if not already installed
if ! npm list -g pm2 &> /dev/null; then
    print_status "Installing global npm packages..."
    npm install -g pm2
else
    print_status "PM2 is already installed globally"
fi

# Create danloo user
print_status "Creating danloo user..."
if ! id "danloo" &>/dev/null; then
    useradd -r -s /bin/bash -m -d /home/danloo danloo
    print_status "Created danloo user with home directory /home/danloo"
else
    print_warning "danloo user already exists"
fi

# Create directory structure
print_status "Setting up /opt/danloo directory..."
if [ -L "/opt/danloo" ]; then
    # /opt/danloo is a symbolic link
    REAL_PATH=$(readlink -f /opt/danloo)
    print_status "/opt/danloo is a symbolic link to $REAL_PATH"

    # Check if target exists
    if [ ! -d "$REAL_PATH" ]; then
        print_error "Symlink target $REAL_PATH does not exist"
        exit 1
    fi

    # Ensure danloo user owns the symlink
    chown -h danloo:danloo /opt/danloo

    # Check if symlink points to a /home directory
    if [[ "$REAL_PATH" == /home/* ]]; then
        print_warning "Symlink points to a /home directory"
        print_warning "You need to ensure the danloo user can access the path:"

        # Extract the home directory (e.g., /home/chenjie)
        HOME_DIR=$(echo "$REAL_PATH" | cut -d'/' -f1-3)
        HOME_PERMS=$(stat -c "%a" "$HOME_DIR" 2>/dev/null || echo "unknown")

        print_warning "  1. Set execute permission on $HOME_DIR (current: $HOME_PERMS)"
        print_warning "     Run: chmod 701 $HOME_DIR"
        print_warning "  2. Or disable ProtectHome in systemd service files"

        # Try to test access
        if sudo -u danloo test -r "$REAL_PATH" 2>/dev/null; then
            print_status "danloo user CAN access $REAL_PATH"
        else
            print_error "danloo user CANNOT access $REAL_PATH"
            print_error "Fix permissions before starting services!"
        fi
    fi

    # Create necessary subdirectories if they don't exist
    sudo -u danloo mkdir -p "$REAL_PATH/frontend/.next" 2>/dev/null || true
    sudo -u danloo mkdir -p "$REAL_PATH/frontend/node_modules/.cache" 2>/dev/null || true

else
    # /opt/danloo is not a symlink, create directory structure
    print_status "Creating directory structure at /opt/danloo..."
    mkdir -p /opt/danloo/{frontend,backend,ai-provider,process,ai-proxy,admin,common,systemdfiles,nginx}
    mkdir -p /opt/danloo/frontend/.next
    mkdir -p /opt/danloo/frontend/node_modules

    # Set ownership
    chown -R danloo:danloo /opt/danloo
    chmod 755 /opt/danloo
fi

# 创建日志目录
print_status "创建日志目录..."
mkdir -p /var/log/danloo
chown -R danloo:danloo /var/log/danloo

# Set .env permissions if it exists
if [ -f "/opt/danloo/.env" ]; then
    chmod 600 /opt/danloo/.env
    chown danloo:danloo /opt/danloo/.env
fi

# Configure firewall (只开放必要的公网端口，内部服务通过 nginx 反向代理)
print_status "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS

# 注意: 内部服务端口 (3000, 8000, 8001, 8002, 8091, 9000) 不对外暴露
# 所有请求通过 nginx 反向代理转发到内部服务
# 如需调试，可临时开放: ufw allow from <your-ip> to any port 8000
print_status "Firewall configured: SSH, HTTP (80), HTTPS (443) allowed"
print_status "Internal service ports are NOT exposed (use nginx reverse proxy)"

# Install certbot for HTTPS (Let's Encrypt)
print_status "Installing certbot for HTTPS..."
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
    print_status "certbot installed"
else
    print_status "certbot is already installed"
fi

# 创建 Let's Encrypt 验证目录
mkdir -p /var/www/html
chown -R www-data:www-data /var/www/html

# 配置 nginx.conf 符号链接 (让 certbot --nginx 可以自动管理)
print_status "Setting up nginx configuration..."
if [ -f "nginx.conf" ]; then
    # 备份原有配置
    if [ -f "/etc/nginx/nginx.conf" ] && [ ! -L "/etc/nginx/nginx.conf" ]; then
        mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
        print_status "Backed up original nginx.conf to nginx.conf.bak"
    fi
    # 删除已有链接
    if [ -L "/etc/nginx/nginx.conf" ]; then
        rm /etc/nginx/nginx.conf
    fi
    # 创建符号链接
    ln -s "$(pwd)/nginx.conf" /etc/nginx/nginx.conf
    print_status "Created symbolic link: /etc/nginx/nginx.conf -> $(pwd)/nginx.conf"
else
    print_warning "nginx.conf not found in current directory"
fi

# Create log rotation configuration
print_status "Setting up log rotation..."
if [ -f "logrotate.conf" ]; then
    cp logrotate.conf /etc/logrotate.d/danloo
    print_status "Log rotation configuration installed from local file"
else
    print_warning "logrotate.conf not found in current directory, skipping"
fi

# Create systemd service directory if not exists
mkdir -p /etc/systemd/system

# Create symbolic links for systemd service files
print_status "Setting up systemd service files..."
services=("danloo-frontend" "danloo-backend" "danloo-ai-provider" "danloo-process" "danloo-ai-proxy" "danloo-admin" "danloo-nginx" "danloo-nginx-minio")

# Check if service files exist in current directory
if [ -f "danloo-frontend.service" ]; then
    for service in "${services[@]}"; do
        service_file="$service.service"
        if [ -f "$service_file" ]; then
            # Remove existing link or file
            if [ -L "/etc/systemd/system/$service_file" ] || [ -f "/etc/systemd/system/$service_file" ]; then
                rm "/etc/systemd/system/$service_file"
                print_warning "Removed existing $service_file"
            fi

            # Create symbolic link
            ln -s "$(pwd)/$service_file" "/etc/systemd/system/$service_file"
            print_status "Created symbolic link for $service_file"
        fi
    done

    # Reload systemd daemon
    systemctl daemon-reload
    print_status "Systemd daemon reloaded"
else
    print_warning "No systemd service files found in current directory"
    print_warning "Run this script from the systemdfiles directory containing .service files"
fi


# Install application dependencies placeholder
print_status "Application dependencies will be installed when you deploy the actual code"
print_status "Please ensure you have the following ready:"
print_status "1. .env file with proper configuration"
print_status "2. Application code in respective directories"
print_status "3. Nginx configuration files"

# =============================================================================
# 健康检查函数
# =============================================================================
health_check() {
    print_status "Running health checks..."
    local all_ok=true

    # 检查必要的命令
    for cmd in node npm python3 uv nginx certbot; do
        if command -v $cmd &> /dev/null; then
            print_status "✓ $cmd: $(command -v $cmd)"
        else
            print_error "✗ $cmd: not found"
            all_ok=false
        fi
    done

    # 检查 danloo 用户
    if id "danloo" &>/dev/null; then
        print_status "✓ danloo user exists"
    else
        print_error "✗ danloo user not found"
        all_ok=false
    fi

    # 检查目录
    if [ -d "/opt/danloo" ] || [ -L "/opt/danloo" ]; then
        print_status "✓ /opt/danloo exists"
    else
        print_error "✗ /opt/danloo not found"
        all_ok=false
    fi

    # 检查防火墙状态
    if ufw status | grep -q "Status: active"; then
        print_status "✓ UFW firewall is active"
    else
        print_warning "⚠ UFW firewall is not active"
    fi

    # 检查日志目录
    if [ -d "/var/log/danloo" ]; then
        print_status "✓ /var/log/danloo exists"
    else
        print_error "✗ /var/log/danloo not found"
        all_ok=false
    fi

    echo ""
    if [ "$all_ok" = true ]; then
        print_status "All health checks passed! ✓"
    else
        print_error "Some health checks failed, please review the errors above"
    fi
}

# 运行健康检查
health_check

print_status "System initialization completed! 🎉"
echo ""
print_status "Next steps:"
echo "1. Copy your application code to /opt/danloo/"
echo "2. Configure /opt/danloo/.env (copy from .env.aliyun)"
echo "3. Install application dependencies:"
echo "   - Frontend: cd /opt/danloo/frontend && npm install && npm run build"
echo "   - Backend services: cd /opt/danloo/backend && uv sync"
echo "4. Start services: systemctl start danloo-frontend danloo-backend etc."
echo "5. Enable services on boot: systemctl enable danloo-frontend danloo-backend etc."
echo "6. Configure HTTPS: certbot --nginx -d danloo.cc -d www.danloo.cc"
echo ""
print_status "System is ready for Danloo deployment!"
