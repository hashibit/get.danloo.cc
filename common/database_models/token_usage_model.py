from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Index
from sqlalchemy.orm import Mapped

from .base import CommonBase


class TokenUsageDB(CommonBase):
    """Token用量信息数据库模型"""

    __tablename__ = "token_usage"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    request_uuid: Mapped[str] = Column(String(36), nullable=False, comment="请求唯一标识")
    consumer: Mapped[str] = Column(String(100), nullable=False, comment="消费者标识 (格式: task:{task_id} 或 job:{job_id})")
    model_id: Mapped[str] = Column(String(100), nullable=False, comment="模型ID")
    prompt_tokens: Mapped[Optional[int]] = Column(Integer, nullable=True, comment="输入token数量")
    completion_tokens: Mapped[Optional[int]] = Column(Integer, nullable=True, comment="输出token数量")
    total_tokens: Mapped[Optional[int]] = Column(Integer, nullable=True, comment="总token数量")
    input_cost: Mapped[Optional[float]] = Column(Numeric(10, 6), nullable=True, comment="输入成本")
    output_cost: Mapped[Optional[float]] = Column(Numeric(10, 6), nullable=True, comment="输出成本")
    total_cost: Mapped[Optional[float]] = Column(Numeric(10, 6), nullable=True, comment="总成本")
    create_time: Mapped[Optional[datetime]] = Column(DateTime, nullable=True, server_default="CURRENT_TIMESTAMP", comment="创建时间")
    update_time: Mapped[Optional[datetime]] = Column(DateTime, nullable=True, server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", comment="更新时间")

    # 设置表级别的索引
    __table_args__ = (
        Index('idx_request_uuid', 'request_uuid'),
        Index('idx_model_id', 'model_id'),
        Index('idx_create_time', 'create_time'),
        {
            'comment': 'Token用量信息宽表',
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_general_ci'
        }
    )

    def __repr__(self) -> str:
        return f"<TokenUsageDB(id={self.id}, request_uuid={self.request_uuid}, model_id={self.model_id}, total_tokens={self.total_tokens})>"