import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from backend.services.rate_limit_service import get_rate_limit_service

logger = logging.getLogger(__name__)


class MailService:
    def __init__(self):
        # Email configuration
        self.smtp_host = os.environ.get("SMTP_HOST", "localhost")
        self.smtp_port = int(
            os.environ.get("SMTP_PORT", "1025")
        )  # Default to mailhog port
        self.smtp_username = os.environ.get("SMTP_USERNAME", "")
        self.smtp_password = os.environ.get("SMTP_PASSWORD", "")
        self.smtp_tls = os.environ.get("SMTP_TLS", "false").lower() == "true"
        self.smtp_ssl = os.environ.get("SMTP_SSL", "false").lower() == "true"
        self.from_email = os.environ.get("FROM_EMAIL", "noreply@danloo.com")
        self.from_name = os.environ.get("FROM_NAME", "丹炉系统")

    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            to_email: Recipient email address
            username: Username of the recipient

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check email rate limiting (2 minutes per email)
            try:
                rate_limit_service = get_rate_limit_service()
                rate_limit_service.check_email_rate_limit(to_email)
            except Exception as e:
                logger.warning(f"Email rate limit exceeded for {to_email}: {str(e)}")
                return False

            # Create message
            msg = MIMEMultipart("alternative")
            # Properly encode non-ASCII characters per RFC5322
            from email.header import Header
            msg["Subject"] = Header("欢迎加入丹炉系统", 'utf-8').encode()
            msg["From"] = f"{Header(self.from_name, 'utf-8').encode()} <{self.from_email}>"
            msg["To"] = to_email

            # Create text and HTML versions of the email
            text_content = f"""
            您好 {username}，

            欢迎加入丹炉系统！

            您已经成功注册了丹炉系统账户，现在可以开始使用了。

            如果您有任何问题，请随时联系我们。

            谢谢！
            丹炉系统团队
            """

            html_content = f"""
            <html>
              <body>
                <h2>欢迎加入丹炉系统！</h2>
                <p>您好 {username}，</p>

                <p>恭喜您成功注册了丹炉系统账户！</p>

                <p>现在您可以开始使用丹炉系统的所有功能了。</p>

                <p>如果您有任何问题，请随时联系我们。</p>

                <p>谢谢！<br>
                丹炉系统团队</p>
              </body>
            </html>
            """

            # Create MIMEText objects
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            # Add parts to message
            msg.attach(part1)
            msg.attach(part2)

            # Send email based on environment
            if os.environ.get("ENVIRONMENT", "production") == "development":
                # In development, just log the email content
                logger.info(f"[development] Welcome email to {to_email}:")
                logger.info(f"Subject: {msg['Subject']}")
                return True
            else:
                # In production, send actual email
                return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
            return False

    def send_email_verification(
        self, to_email: str, verification_token: str, username: str
    ) -> bool:
        """
        Send email verification link to user.

        Args:
            to_email: Recipient email address
            verification_token: Email verification token
            username: Username of the recipient

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check email rate limiting (2 minutes per email)
            try:
                rate_limit_service = get_rate_limit_service()
                rate_limit_service.check_email_rate_limit(to_email)
            except Exception as e:
                logger.warning(f"Email rate limit exceeded for {to_email}: {str(e)}")
                return False

            # Create verification link
            verification_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/verify-email?token={verification_token}"

            # Create message
            msg = MIMEMultipart("alternative")
            # Properly encode non-ASCII characters per RFC5322
            from email.header import Header
            msg["Subject"] = Header("丹炉系统 - 验证您的邮箱", 'utf-8').encode()
            msg["From"] = f"{Header(self.from_name, 'utf-8').encode()} <{self.from_email}>"
            msg["To"] = to_email

            # Create text and HTML versions of the email
            text_content = f"""
            您好 {username}，

            感谢您注册丹炉系统！

            请点击以下链接验证您的邮箱地址：
            {verification_link}

            如果您没有注册丹炉系统账户，请忽略这封邮件。

            此链接将在24小时后过期。

            谢谢！
            丹炉系统团队
            """

            html_content = f"""
            <html>
              <body>
                <h2>丹炉系统 - 验证您的邮箱</h2>
                <p>您好 {username}，</p>

                <p>感谢您注册丹炉系统！</p>

                <p>请点击以下链接验证您的邮箱地址：</p>
                <p><a href="{verification_link}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>

                <p>或者复制以下链接到浏览器：</p>
                <p style="color: #666;">{verification_link}</p>

                <p>如果您没有注册丹炉系统账户，请忽略这封邮件。</p>

                <p><strong>注意：</strong>此链接将在24小时后过期。</p>

                <p>谢谢！<br>
                丹炉系统团队</p>
              </body>
            </html>
            """

            # Create MIMEText objects
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            # Add parts to message
            msg.attach(part1)
            msg.attach(part2)

            # Send email based on environment
            if os.environ.get("ENVIRONMENT", "production") == "development":
                # In development, just log the email content
                logger.info(f"[development] Email verification email to {to_email}:")
                logger.info(f"Subject: {msg['Subject']}")
                logger.info(f"Verification link: {verification_link}")
                return True
            else:
                # In production, send actual email
                return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send email verification to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(
        self, to_email: str, reset_token: str, username: str
    ) -> bool:
        """
        Send password reset email to user.

        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            username: Username of the recipient

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check email rate limiting (2 minutes per email)
            try:
                rate_limit_service = get_rate_limit_service()
                rate_limit_service.check_email_rate_limit(to_email)
            except Exception as e:
                logger.warning(f"Email rate limit exceeded for {to_email}: {str(e)}")
                return False

            # Create reset link
            reset_link = f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

            # Create message
            msg = MIMEMultipart("alternative")
            # Properly encode non-ASCII characters per RFC5322
            from email.header import Header
            msg["Subject"] = Header("丹炉系统 - 密码重置请求", 'utf-8').encode()
            msg["From"] = f"{Header(self.from_name, 'utf-8').encode()} <{self.from_email}>"
            msg["To"] = to_email

            # Create text and HTML versions of the email
            text_content = f"""
            您好 {username}，

            您收到这封邮件是因为您请求重置丹炉系统的密码。

            请点击以下链接重置您的密码：
            {reset_link}

            如果您没有请求密码重置，请忽略这封邮件。

            此链接将在15分钟后过期。

            谢谢！
            丹炉系统团队
            """

            html_content = f"""
            <html>
              <body>
                <h2>丹炉系统 - 密码重置请求</h2>
                <p>您好 {username}，</p>

                <p>您收到这封邮件是因为您请求重置丹炉系统的密码。</p>

                <p>请点击以下链接重置您的密码：</p>
                <p><a href="{reset_link}">重置密码</a></p>

                <p>如果您没有请求密码重置，请忽略这封邮件。</p>

                <p><strong>注意：</strong>此链接将在15分钟后过期。</p>

                <p>谢谢！<br>
                丹炉系统团队</p>
              </body>
            </html>
            """

            # Create MIMEText objects
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")

            # Add parts to message
            msg.attach(part1)
            msg.attach(part2)

            # Send email based on environment
            if os.environ.get("ENVIRONMENT", "production") == "development":
                # In development, just log the email content
                logger.info(f"[development] Password reset email to {to_email}:")
                logger.info(f"Subject: {msg['Subject']}")
                logger.info(f"Reset link: {reset_link}")
                return True
            else:
                # In production, send actual email
                return self._send_email(msg)

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """
        Send email using SMTP.

        Args:
            msg: Email message to send

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create SMTP connection
            if self.smtp_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                if self.smtp_tls:
                    server.starttls()

            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            # Send email
            server.send_message(msg)
            server.quit()

            logger.info(f"[production] Email sent successfully to {msg['To']}")
            return True

        except Exception as e:
            logger.error(f"[production] Failed to send email: {str(e)}")
            return False
