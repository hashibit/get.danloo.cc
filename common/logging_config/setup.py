"""
日志设置功能模块
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    service_name: str,
    level: str = "INFO",
    format_string: Optional[str] = None,
    enable_file: bool = False,
    log_dir: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    设置统一的日志配置
    
    Args:
        service_name: 服务名称（如 'backend', 'process', 'ai-provider'）
        level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        format_string: 自定义日志格式
        enable_file: 是否启用文件日志
        log_dir: 日志目录，默认为 '/var/log/danloo'
        max_file_size: 日志文件最大大小（字节）
        backup_count: 备份文件数量
    
    Returns:
        配置好的 logger 对象
    """
    
    # 默认格式：时间 - 服务名 - 模块名 - 级别 - 消息
    if format_string is None:
        format_string = f"%(asctime)s - [{service_name}] - %(name)s - %(levelname)s - %(message)s"
    
    # 获取根 logger
    root_logger = logging.getLogger()
    
    # 清除现有处理器（避免重复配置）
    root_logger.handlers.clear()
    
    # 设置日志级别
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # 创建格式化器
    formatter = logging.Formatter(format_string)
    
    # 控制台处理器（始终启用）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（可选）
    if enable_file:
        try:
            # 设置默认日志目录
            if log_dir is None:
                log_dir = "/var/log/danloo"
            
            # 创建日志目录
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            
            # 日志文件路径
            log_file = log_path / f"{service_name}.log"
            
            # 使用轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_file),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            # 文件日志失败时记录警告，但继续运行
            root_logger.warning(
                f"Cannot create log file in {log_dir}: {e}. File logging disabled."
            )
    
    # 设置第三方库的日志级别（避免过多噪音）
    _configure_third_party_loggers(service_name)
    
    # 返回主服务的 logger
    return logging.getLogger(service_name)


def setup_basic_logging(service_name: str, level: str = "INFO") -> logging.Logger:
    """简化版本，类似于 logging.basicConfig"""
    return setup_logging(
        service_name=service_name,
        level=level,
        enable_file=False  # 默认不启用文件日志
    )


def _configure_third_party_loggers(service_name: str) -> None:
    """配置第三方库的日志级别，减少噪音"""
    # 设置 httpx 为 WARNING 级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # 设置 uvicorn 访问日志级别
    if service_name != "ai-provider":  # ai-provider 可能需要更详细的日志
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)