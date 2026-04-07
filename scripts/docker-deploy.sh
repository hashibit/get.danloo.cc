#!/bin/bash

# 丹炉 (Danloo) Platform Docker 部署工具
# 提供构建、导出、传输和加载 Docker 镜像的功能

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

# 显示帮助信息
show_help() {
    echo "丹炉 (Danloo) Platform Docker 部署工具"
    echo ""
    echo "用法: $0 [子命令] [参数]"
    echo ""
    echo "子命令:"
    echo "  build [aliyun]     构建所有服务的 Docker 镜像"
    echo "  export [aliyun]    将构建的镜像导出为 tar 文件"
    echo "  transfer           通过 scp 将镜像传输到远程服务器"
    echo "  load               在远程服务器上加载所有镜像到 Docker"
    echo "  clean              清理导出的镜像文件"
    echo "  help               显示此帮助信息"
    echo ""
    echo "参数:"
    echo "  aliyun             使用阿里云配置（docker-compose-aliyun.yml）"
    echo ""
    echo "示例:"
    echo "  $0 build"
    echo "  $0 build aliyun"
    echo "  $0 export aliyun"
    echo "  $0 transfer user@server:/path/to/destination"
    echo "  $0 load user@server"
}

# 构建所有服务的 Docker 镜像
build_images() {
    local use_aliyun=$1
    
    if [ "$use_aliyun" = "aliyun" ]; then
        log_info "开始构建 Docker 镜像 (阿里云配置)..."
        docker compose -f docker-compose-aliyun.yml build
    else
        log_info "开始构建 Docker 镜像 (本地配置)..."
        docker compose build
    fi

    log_success "所有 Docker 镜像构建完成"
}

# 导出构建的镜像为 tar 文件
export_images() {
    local use_aliyun=$1
    
    if [ "$use_aliyun" = "aliyun" ]; then
        log_info "开始导出 Docker 镜像 (阿里云配置)..."
        compose_file="docker-compose-aliyun.yml"
    else
        log_info "开始导出 Docker 镜像 (本地配置)..."
        compose_file="docker-compose.yml"
    fi

    # 创建导出目录
    mkdir -p docker-images

    # 导出需要构建的服务镜像
    services=("backend" "ai-provider" "ai-proxy" "process" "frontend" "admin")

    for service in "${services[@]}"; do
        log_info "导出 $service 镜像..."
        # Docker Compose 使用 项目目录名-service名 作为镜像名称
        image_name="danloo-$service"
        if [ "$use_aliyun" = "aliyun" ]; then
            docker compose -f $compose_file build $service
        else
            docker compose build $service
        fi
        docker save $image_name | gzip > docker-images/$service.tar.gz
    done

    # 导出现成的镜像
    log_info "导出 nginx 镜像..."
    docker pull nginx:alpine
    docker save nginx:alpine | gzip > docker-images/nginx.tar.gz

    log_success "所有 Docker 镜像导出完成"
    log_info "镜像文件保存在 docker-images 目录中"
}

# 通过 scp 将镜像传输到远程服务器
transfer_images() {
    if [ -z "$1" ]; then
        log_error "请提供远程服务器地址和目标路径"
        log_info "用法: $0 transfer user@server:/path/to/destination"
        exit 1
    fi

    local remote_path=$1
    log_info "开始传输 Docker 镜像到 $remote_path..."

    # 检查 docker-images 目录是否存在
    if [ ! -d "docker-images" ]; then
        log_error "docker-images 目录不存在，请先运行 export 命令"
        exit 1
    fi

    # 传输所有镜像文件
    scp docker-images/*.tar.gz $remote_path

    log_success "Docker 镜像传输完成"
}

# 在远程服务器上加载所有镜像到 Docker
load_images() {
    if [ -z "$1" ]; then
        log_error "请提供远程服务器地址"
        log_info "用法: $0 load user@server"
        exit 1
    fi

    local remote_server=$1
    log_info "开始在 $remote_server 上加载 Docker 镜像..."

    # 检查 docker-images 目录是否存在
    if [ ! -d "docker-images" ]; then
        log_error "docker-images 目录不存在，请先运行 export 命令"
        exit 1
    fi

    # 获取所有镜像文件名
    images=$(ls docker-images/*.tar.gz | xargs -n 1 basename)

    # 在远程服务器上加载每个镜像
    for image in $images; do
        log_info "加载镜像 $image..."
        ssh $remote_server "docker load -i docker-images/$image"
    done

    log_success "所有 Docker 镜像加载完成"
}

# 清理导出的镜像文件
clean_images() {
    log_info "清理导出的镜像文件..."

    if [ -d "docker-images" ]; then
        rm -rf docker-images
        log_success "镜像文件清理完成"
    else
        log_info "docker-images 目录不存在，无需清理"
    fi
}

# 主函数
main() {
    case "$1" in
        build)
            build_images "$2"
            ;;
        export)
            export_images "$2"
            ;;
        transfer)
            transfer_images "$2"
            ;;
        load)
            load_images "$2"
            ;;
        clean)
            clean_images
            ;;
        help)
            show_help
            ;;
        *)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
