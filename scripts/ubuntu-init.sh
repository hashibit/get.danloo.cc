#!/bin/bash

# 丹炉 (Danloo) Platform - Ubuntu 24.04 系统初始化脚本
# 用于安装和配置 Docker、Docker Compose 以及其他必要依赖

set -e  # 出错时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 Ubuntu 24.04
check_ubuntu_version() {
    log_info "检查 Ubuntu 版本..."
    if ! command -v lsb_release &> /dev/null; then
        log_error "无法确定 Ubuntu 版本，lsb_release 命令不可用"
        exit 1
    fi

    local version=$(lsb_release -rs)
    if [[ "$version" != "24.04" ]]; then
        log_warning "此脚本专为 Ubuntu 24.04 设计，当前版本: $version"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "退出安装"
            exit 1
        fi
    else
        log_success "Ubuntu 版本正确: $version"
    fi
}

# 更新系统包列表
update_system() {
    log_info "更新系统包列表..."
    sudo apt update
    log_success "系统包列表更新完成"
}

# 安装必要系统依赖
install_system_dependencies() {
    log_info "安装系统依赖..."
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        software-properties-common \
        git \
        wget
    log_success "系统依赖安装完成"
}

# 安装 Docker
install_docker() {
    log_info "安装 Docker..."

    # 添加 Docker 官方 GPG 密钥
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # 添加 Docker 仓库
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # 更新包列表并安装 Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    log_success "Docker 安装完成"
}

# 启动并启用 Docker 服务
enable_docker() {
    log_info "启动并启用 Docker 服务..."
    sudo systemctl start docker
    sudo systemctl enable docker
    log_success "Docker 服务已启动并设置为开机自启"
}

# 将当前用户添加到 docker 组
add_user_to_docker_group() {
    log_info "将当前用户添加到 docker 组..."
    sudo usermod -aG docker $USER
    log_success "用户已添加到 docker 组"
}

# 验证 Docker 安装
verify_docker() {
    log_info "验证 Docker 安装..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 安装失败"
        exit 1
    fi

    # 检查 Docker 版本
    local docker_version=$(docker --version)
    log_success "Docker 版本: $docker_version"

    # 检查 Docker Compose 版本
    if command -v docker compose &> /dev/null; then
        local compose_version=$(docker compose version)
        log_success "Docker Compose 版本: $compose_version"
    else
        log_error "Docker Compose 未正确安装"
        exit 1
    fi
}

# 克隆项目仓库（如果需要）
clone_repository() {
    if [ ! -d "danloo" ]; then
        log_info "克隆 Danloo 项目仓库..."
        git clone https://github.com/hashipod/danloo.git
        cd danloo
        log_success "项目克隆完成"
    else
        log_info "Danloo 项目目录已存在"
    fi
}

# 主函数
main() {
    log_info "开始初始化 Ubuntu 系统以部署 Danloo 平台..."

    check_ubuntu_version
    update_system
    install_system_dependencies
    install_docker
    enable_docker
    add_user_to_docker_group
    verify_docker
    clone_repository

    log_success "系统初始化完成!"
    log_info "请执行以下操作以完成部署:"
    log_info "1. 配置 .env 文件（如果需要）:"
    log_info "   cp .env.example .env && nano .env"
    log_info "2. 启动服务:"
    log_info "   docker compose up --build"
    log_info "注意: 您可能需要重新登录或运行 'newgrp docker' 命令来激活 docker 组权限"
}

# 执行主函数
main "$@"
