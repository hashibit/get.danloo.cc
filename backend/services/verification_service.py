import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from common.database_models.verification_code_model import VerificationCode
from common.logging_config import get_logger
from backend.services.rate_limit_service import get_rate_limit_service

logger = get_logger(__name__)


class VerificationService:
    def generate_verification_code(self, length: int = 6) -> str:
        """生成指定长度的数字验证码"""
        return ''.join(random.choices(string.digits, k=length))

    async def send_verification_code(
        self,
        db: Session,
        phone_number: str,
        code_type: str = 'login',
        code_length: int = 6,
        expire_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        发送验证码

        Args:
            phone_number: 手机号
            code_type: 验证码类型 ('login', 'register', 'phone_verification')
            code_length: 验证码长度
            expire_minutes: 过期时间(分钟)

        Returns:
            Dict: 发送结果
        """
        try:
            # 验证手机号格式
            if not self._validate_phone_number(phone_number):
                return {
                    'success': False,
                    'message': '手机号格式不正确'
                }

            # 检查发送频率限制 (2分钟一次)
            try:
                rate_limit_service = get_rate_limit_service()
                rate_limit_service.check_sms_rate_limit(phone_number)
            except Exception as e:
                return {
                    'success': False,
                    'message': f'发送频率限制：{str(e)}'
                }

            # 生成验证码
            code = self.generate_verification_code(code_length)
            expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)

            # 清理该手机号同类型的未使用验证码
            db.query(VerificationCode).filter(
                and_(
                    VerificationCode.phone_number == phone_number,
                    VerificationCode.type == code_type,
                    VerificationCode.is_used == False,
                    VerificationCode.expires_at > datetime.utcnow()
                )
            ).update({
                'is_used': True,
                'updated_at': datetime.utcnow()
            })

            # 保存验证码到数据库
            verification_code = VerificationCode(
                phone_number=phone_number,
                code=code,
                type=code_type,
                expires_at=expires_at,
                is_used=False,
                attempts=0
            )
            db.add(verification_code)
            db.commit()

            # 发送验证码 (这里需要集成实际的短信服务)
            await self._send_sms(phone_number, code, code_type)

            logger.info(f"验证码已发送到 {phone_number}, 类型: {code_type}")

            return {
                'success': True,
                'message': '验证码已发送',
                'verification_id': str(verification_code.id)
            }

        except Exception as e:
            logger.error(f"发送验证码失败: {str(e)}")
            return {
                'success': False,
                'message': '发送验证码失败，请重试'
            }

    async def verify_code(
        self,
        db: Session,
        phone_number: str,
        code: str,
        code_type: str = 'login'
    ) -> Dict[str, Any]:
        """
        验证验证码

        Args:
            phone_number: 手机号
            code: 验证码
            code_type: 验证码类型

        Returns:
            Dict: 验证结果
        """
        try:
            # 查找有效的验证码
            verification_code = db.query(VerificationCode).filter(
                and_(
                    VerificationCode.phone_number == phone_number,
                    VerificationCode.code == code,
                    VerificationCode.type == code_type,
                    VerificationCode.is_used == False,
                    VerificationCode.expires_at > datetime.utcnow()
                )
            ).first()

            if not verification_code:
                return {
                    'success': False,
                    'message': '验证码无效或已过期'
                }

            # 检查尝试次数
            if verification_code.attempts >= 3:
                verification_code.is_used = True
                db.commit()
                return {
                    'success': False,
                    'message': '验证码错误次数过多，请重新获取'
                }

            # 增加尝试次数
            verification_code.attempts += 1
            db.commit()

            # 验证成功
            verification_code.is_used = True
            db.commit()

            logger.info(f"验证码验证成功: {phone_number}, 类型: {code_type}")

            return {
                'success': True,
                'message': '验证码验证成功'
            }

        except Exception as e:
            logger.error(f"验证验证码失败: {str(e)}")
            return {
                'success': False,
                'message': '验证失败，请重试'
            }

    def _validate_phone_number(self, phone_number: str) -> bool:
        """验证手机号格式"""
        # 简单的中国手机号验证
        return bool(phone_number and len(phone_number) == 11 and phone_number.startswith('1'))

    async def _check_rate_limit(self, db: Session, phone_number: str, code_type: str) -> bool:
        """检查发送频率限制"""
        # 检查1分钟内是否已发送过同类型验证码
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_code = db.query(VerificationCode).filter(
            and_(
                VerificationCode.phone_number == phone_number,
                VerificationCode.type == code_type,
                VerificationCode.created_at > one_minute_ago
            )
        ).first()

        return recent_code is None

    async def _send_sms(self, phone_number: str, code: str, code_type: str):
        """
        发送短信 (需要集成实际的短信服务)

        这里是一个示例实现，实际使用时需要替换为真实的短信服务API
        """
        # 示例短信内容
        if code_type == 'login':
            message = f"【丹炉】您的登录验证码是：{code}，5分钟内有效，请勿泄露给他人。"
        elif code_type == 'register':
            message = f"【丹炉】您的注册验证码是：{code}，5分钟内有效，请勿泄露给他人。"
        else:
            message = f"【丹炉】您的验证码是：{code}，5分钟内有效，请勿泄露给他人。"

        # TODO: 集成实际的短信服务
        # 例如：阿里云短信、腾讯云短信、Twilio等
        logger.info(f"SMS would be sent to {phone_number}: {message}")

        # 示例：使用阿里云短信服务
        # from aliyunsdkcore.client import AcsClient
        # from aliyunsdkcore.request import CommonRequest
        #
        # client = AcsClient(
        #     access_key_id=os.getenv('ALIYUN_ACCESS_KEY_ID'),
        #     access_key_secret=os.getenv('ALIYUN_ACCESS_KEY_SECRET'),
        #     region_id='cn-hangzhou'
        # )
        #
        # request = CommonRequest()
        # request.set_method('POST')
        # request.set_domain('dysmsapi.aliyuncs.com')
        # request.set_version('2017-05-25')
        # request.set_action_name('SendSms')
        # request.add_query_param('PhoneNumbers', phone_number)
        # request.add_query_param('SignName', '丹炉')
        # request.add_query_param('TemplateCode', 'SMS_123456789')
        # request.add_query_param('TemplateParam', f'{{"code":"{code}"}}')
        #
        # response = client.do_action_with_exception(request)
        # logger.info(f"SMS response: {response}")

    def cleanup_expired_codes(self, db: Session):
        """清理过期的验证码"""
        try:
            db.query(VerificationCode).filter(
                VerificationCode.expires_at < datetime.utcnow()
            ).delete()
            db.commit()
            logger.info("清理过期验证码完成")
        except Exception as e:
            logger.error(f"清理过期验证码失败: {str(e)}")


def get_verification_service() -> VerificationService:
    """获取验证码服务实例"""
    return VerificationService()
