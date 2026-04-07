from sqlalchemy.orm import Session
from common.database_models.crypto_keys_model import CryptoKeysDB
from common.api_models.crypto_keys_model import CryptoKeysResponse
from common.api_models.user_model import UserCreate, PhoneRegisterRequest, PhoneLoginRequest, WeChatLoginRequest, UserResponse, UserProfileResponse, SocialAccountResponse
from common.database_models.user_model import UserDB
from common.database_models.social_account_model import SocialAccountDB

from backend.middleware.auth import create_access_token
from backend.services.verification_service import get_verification_service
from backend.services.wechat_service import get_wechat_service
from backend.services.secret_service import SecretService
from backend.services.quota_service import get_quota_service
from backend.services.mail_service import MailService
from common.crypto.services.password_hash import PasswordHashService
from common.utils.ulid_utils import generate_ulid

import os
import json
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        self.secret_key = os.environ.get("JWT_SECRET", "your-secret-key")
        self.algorithm = "HS256"
        self.secret_service = SecretService()
        self.password_service = PasswordHashService()
        self.verification_service = None
        self.wechat_service = None
        self.quota_service = None

    def _get_verification_service(self):
        """Get verification service instance"""
        if self.verification_service is None:
            self.verification_service = get_verification_service()
        return self.verification_service

    def _get_wechat_service(self):
        """Get WeChat service instance"""
        if self.wechat_service is None:
            self.wechat_service = get_wechat_service()
        return self.wechat_service

    def _get_quota_service(self):
        """Get quota service instance"""
        if self.quota_service is None:
            self.quota_service = get_quota_service()
        return self.quota_service

    def create_user(self, db: Session, user_data: UserCreate) -> UserDB:
        """Create a new user in the database with crypto keys"""
        try:
            # Check if user already exists
            existing_user = (
                db.query(UserDB)
                .filter(
                    (UserDB.email == user_data.email)
                    | (UserDB.username == user_data.username)
                )
                .first()
            )

            if existing_user:
                raise ValueError("User with this email or username already exists")

            # Validate password strength
            password_validation = self.password_service.validate_password_strength(
                user_data.password
            )
            if not password_validation.is_valid:
                raise ValueError(
                    f"Password requirements not met: {password_validation.error}"
                )

            # Create user record first (without password hash)
            new_user = UserDB(
                email=user_data.email,
                username=user_data.username,
                password_hash="",  # Will be set after crypto keys are created
                exp_level="初级",
            )

            db.add(new_user)
            db.flush()  # Get user ID without committing

            # Create crypto keys for the user
            crypto_keys = self.secret_service.create_user_crypto_keys(db, new_user.id)

            # Hash password using the generated salt
            hashed_password = self.password_service.hash_password(
                user_data.password, crypto_keys.salt
            )

            # Update user with hashed password
            new_user.password_hash = hashed_password

            # Initialize default quota for new user
            quota_service = self._get_quota_service()
            try:
                quota_service.get_user_quota(db, new_user.id, "credits")
                logger.info(f"Initialized default quota for user {new_user.id}")
            except Exception as quota_error:
                logger.error(f"Failed to initialize quota for user {new_user.id}: {str(quota_error)}")
                # Don't fail user creation if quota initialization fails

            db.commit()
            db.refresh(new_user)

            logger.info(f"Created user {new_user.id} with crypto keys and quota")
            
            # Send welcome email asynchronously
            try:
                import asyncio
                from .mail_service import MailService
                mail_service = MailService()
                
                # Run email sending in background
                asyncio.create_task(
                    self._send_welcome_email_async(mail_service, new_user.email, new_user.username)
                )
            except Exception as email_error:
                logger.warning(f"Failed to queue welcome email for user {new_user.id}: {email_error}")
                # Don't fail user creation if email fails
            
            return new_user

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            db.rollback()
            raise

    async def _send_welcome_email_async(self, mail_service, email: str, username: str):
        """Send welcome email asynchronously"""
        try:
            success = mail_service.send_welcome_email(email, username)
            if success:
                logger.info(f"Welcome email sent successfully to {email}")
            else:
                logger.warning(f"Failed to send welcome email to {email}")
        except Exception as e:
            logger.error(f"Error sending welcome email to {email}: {str(e)}")

    def authenticate_user(self, db: Session, email: str, password: str) -> str:
        """Authenticate user and return access token"""
        user = db.query(UserDB).filter(UserDB.email == email).first()

        if not user:
            raise ValueError("User not found")

        # Check password using crypto service
        if self.secret_service.verify_user_password(db, user.id, password):
            # Create access token
            token_data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
            }
            access_token = create_access_token(token_data)
            return access_token
        else:
            raise ValueError("Invalid credentials")

    def get_user_by_id(self, db: Session, user_id: str) -> UserDB | None:
        """Get user by ID from database"""
        return db.query(UserDB).filter(UserDB.id == user_id).first()

    def get_user_with_quota(self, db: Session, user_id: str) -> UserResponse | None:
        """Get user with current quota information"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None

        # Get user's current quota
        quota_service = self._get_quota_service()
        try:
            quota_status = quota_service.get_current_quota_status(db, user_id, "credits")
            quota_dict = {
                "quota_type": quota_status.quota_type,
                "daily_limit": quota_status.daily_limit,
                "used_amount": quota_status.used_amount,
                "remaining_amount": quota_status.remaining_amount,
                "usage_percentage": quota_status.usage_percentage,
                "reset_date": quota_status.reset_date.isoformat(),
                "is_active": quota_status.is_active
            }
        except Exception as e:
            logger.error(f"Failed to get quota for user {user_id}: {str(e)}")
            quota_dict = None

        # Convert user to dict and add quota info
        user_response = UserResponse.model_validate(user)
        user_response.current_quota = quota_dict

        return user_response

    def get_user_profile_with_social_accounts(self, db: Session, user_id: str) -> UserProfileResponse | None:
        """Get user profile with social accounts information"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None

        # Get social accounts
        social_accounts = db.query(SocialAccountDB).filter(
            SocialAccountDB.user_id == user_id
        ).all()

        # Build response
        profile_data = UserProfileResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            exp_level=user.exp_level,
            phone_number=user.phone_number,
            phone_verified=user.phone_verified,
            wechat_nickname=user.wechat_nickname,
            wechat_avatar=user.wechat_avatar,
            created_at=user.created_at,
            updated_at=user.updated_at,
            email_verified=user.email_verified if user.email else False,
            social_accounts=[]
        )

        # Add social accounts
        for account in social_accounts:
            social_account_data = SocialAccountResponse(
                provider=account.provider,
                account_id=account.provider_user_id,
                nickname=None,
                avatar=None,
                linked_at=account.created_at
            )

            # Extract nickname and avatar from raw_data if available
            if account.raw_data:
                if account.provider == 'wechat':
                    social_account_data.nickname = account.raw_data.get("nickname")
                    social_account_data.avatar = account.raw_data.get("headimgurl")
                elif account.provider == 'github':
                    social_account_data.nickname = account.raw_data.get("login")
                    social_account_data.avatar = account.raw_data.get("avatar_url")
                elif account.provider == 'google':
                    social_account_data.nickname = account.raw_data.get("name")
                    social_account_data.avatar = account.raw_data.get("picture")

            profile_data.social_accounts.append(social_account_data)

        return profile_data

    def get_user_by_email(self, db: Session, email: str) -> UserDB | None:
        """Get user by email from database"""
        return db.query(UserDB).filter(UserDB.email == email).first()

    def get_user_crypto_keys(self, db: Session, user_id: str) -> CryptoKeysResponse | None:
        """Get user's crypto keys (returns only safe fields)"""

        crypto_keys = self.secret_service.get_user_crypto_keys(db, user_id)
        if crypto_keys:
            return CryptoKeysResponse(
                user_id=crypto_keys.user_id,
                access_key=crypto_keys.access_key,
                created_at=crypto_keys.created_at,
                updated_at=crypto_keys.updated_at,
            )
        return None

    def rotate_user_crypto_keys(self, db: Session, user_id: str) -> CryptoKeysDB:
        """Rotate user's crypto keys"""
        return self.secret_service.rotate_user_keys(db, user_id)

    async def send_verification_code(self, db: Session, phone_number: str, code_type: str = "login"):
        """Send verification code to phone number"""
        verification_service = self._get_verification_service()
        return await verification_service.send_verification_code(db, phone_number, code_type)

    async def verify_code(self, db: Session, phone_number: str, code: str, code_type: str = "login"):
        """Verify verification code"""
        verification_service = self._get_verification_service()
        return await verification_service.verify_code(db, phone_number, code, code_type)

    async def create_user_with_phone(self, db: Session, user_data: PhoneRegisterRequest) -> UserDB:
        """Create a new user with phone number"""
        try:
            # Verify the verification code
            if not await self.verify_code(db, user_data.phone_number, user_data.verification_code, "register"):
                raise ValueError("Invalid verification code")

            # Check if user already exists
            existing_user = db.query(UserDB).filter(
                (UserDB.phone_number == user_data.phone_number) |
                (UserDB.username == user_data.username)
            ).first()

            if existing_user:
                raise ValueError("User with this phone number or username already exists")

            # Create user record
            new_user = UserDB(
                username=user_data.username,
                phone_number=user_data.phone_number,
                phone_verified=True,
                exp_level="初级",
            )

            # If password is provided, hash it
            if user_data.password:
                # Create crypto keys first
                crypto_keys = self.secret_service.create_user_crypto_keys(db, new_user.id)
                hashed_password = self.password_service.hash_password(
                    user_data.password, crypto_keys.salt
                )
                new_user.password_hash = hashed_password
            else:
                # For phone-only users, still create crypto keys for API access
                self.secret_service.create_user_crypto_keys(db, new_user.id)

            db.add(new_user)
            db.flush()  # Get user ID

            # Initialize default quota for new user
            quota_service = self._get_quota_service()
            try:
                quota_service.get_user_quota(db, new_user.id, "credits")
                logger.info(f"Initialized default quota for user {new_user.id}")
            except Exception as quota_error:
                logger.error(f"Failed to initialize quota for user {new_user.id}: {str(quota_error)}")
                # Don't fail user creation if quota initialization fails

            db.commit()
            db.refresh(new_user)

            logger.info(f"Created user {new_user.id} with phone number and quota")
            return new_user

        except Exception as e:
            logger.error(f"Failed to create user with phone: {str(e)}")
            db.rollback()
            raise

    async def authenticate_user_with_phone(self, db: Session, phone_number: str, verification_code: str) -> str:
        """Authenticate user with phone number and verification code"""
        try:
            # Verify the verification code
            if not await self.verify_code(db, phone_number, verification_code, "login"):
                raise ValueError("Invalid verification code")

            # Find user by phone number
            user = db.query(UserDB).filter(UserDB.phone_number == phone_number).first()

            if not user:
                # Auto-register user if not found
                # Generate username from phone number
                username = f"phone_user_{phone_number[-4:]}"

                # Check if username exists, append number if needed
                original_username = username
                counter = 1
                while db.query(UserDB).filter(UserDB.username == username).first():
                    username = f"{original_username}_{counter}"
                    counter += 1

                # Create new user
                user = UserDB(
                    id=generate_ulid(),
                    username=username,
                    phone_number=phone_number,
                    phone_verified=True,
                    exp_level="初级",
                )

                # Create crypto keys for the user
                self.secret_service.create_user_crypto_keys(db, user.id)

                db.add(user)
                db.commit()
                db.refresh(user)

                logger.info(f"Auto-registered new user {user.id} with phone number")

            # Update phone verified status
            if not user.phone_verified:
                user.phone_verified = True
                db.commit()

            # Create access token
            token_data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "phone_number": user.phone_number,
            }
            access_token = create_access_token(token_data)
            return access_token

        except Exception as e:
            logger.error(f"Failed to authenticate user with phone: {str(e)}")
            raise

    async def authenticate_with_wechat(self, db: Session, wechat_data: WeChatLoginRequest) -> dict:
        """Authenticate user with WeChat"""
        try:
            # Authenticate with WeChat
            wechat_service = self._get_wechat_service()
            wechat_result = await wechat_service.handle_wechat_login(wechat_data.code, wechat_data.state)
            if not wechat_result.get("success"):
                raise ValueError("WeChat authentication failed")

            wechat_user_data = wechat_result.get("data", {})
            openid = wechat_user_data.get("openid")
            unionid = wechat_user_data.get("unionid")
            nickname = wechat_user_data.get("nickname")
            avatar = wechat_user_data.get("headimgurl")

            # Find user by WeChat openid
            user = db.query(UserDB).filter(UserDB.wechat_openid == openid).first()
            is_new_user = False

            if not user:
                # Create new user
                is_new_user = True

                # Generate username from nickname or use default
                username = nickname or f"wx_user_{openid[:8]}"

                # Check if username exists, append number if needed
                original_username = username
                counter = 1
                while db.query(UserDB).filter(UserDB.username == username).first():
                    username = f"{original_username}_{counter}"
                    counter += 1

                # Create new user
                user = UserDB(
                    username=username,
                    wechat_openid=openid,
                    wechat_unionid=unionid,
                    wechat_nickname=nickname,
                    wechat_avatar=avatar,
                    exp_level="初级",
                )

                db.add(user)
                db.flush()  # Get user ID without committing

                # Create crypto keys for the user
                self.secret_service.create_user_crypto_keys(db, user.id)

                # Create social account record
                social_account = SocialAccountDB(
                    user_id=user.id,
                    provider='wechat',
                    provider_user_id=openid,
                    access_token=wechat_user_data.get('access_token'),
                    refresh_token=wechat_user_data.get('refresh_token'),
                    scope=wechat_user_data.get('scope'),
                    raw_data=wechat_user_data  # Store all WeChat data as JSON
                )
                db.add(social_account)

                db.commit()
                db.refresh(user)

                logger.info(f"Created new user {user.id} from WeChat login")
            else:
                # Update WeChat info if changed
                if (user.wechat_nickname != nickname or
                    user.wechat_avatar != avatar):
                    user.wechat_nickname = nickname
                    user.wechat_avatar = avatar

                # Update or create social account record
                social_account = db.query(SocialAccountDB).filter(
                    SocialAccountDB.user_id == user.id,
                    SocialAccountDB.provider == 'wechat'
                ).first()

                if social_account:
                    # Update existing social account
                    social_account.access_token = wechat_user_data.get('access_token')
                    social_account.refresh_token = wechat_user_data.get('refresh_token')
                    social_account.scope = wechat_user_data.get('scope')
                    social_account.raw_data = wechat_user_data
                else:
                    # Create new social account record
                    social_account = SocialAccountDB(
                        user_id=user.id,
                        provider='wechat',
                        provider_user_id=openid,
                        access_token=wechat_user_data.get('access_token'),
                        refresh_token=wechat_user_data.get('refresh_token'),
                        scope=wechat_user_data.get('scope'),
                        raw_data=wechat_user_data
                    )
                    db.add(social_account)

                db.commit()
                db.refresh(user)

                logger.info(f"Existing user {user.id} logged in with WeChat")

            # Create access token
            token_data = {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "wechat_openid": user.wechat_openid,
            }
            access_token = create_access_token(token_data)

            return {
                "access_token": access_token,
                "user": user,
                "is_new_user": is_new_user
            }

        except Exception as e:
            logger.error(f"Failed to authenticate with WeChat: {str(e)}")
            raise

    async def link_phone_to_user(self, db: Session, user_id: str, phone_number: str, verification_code: str) -> bool:
        """Link phone number to existing user"""
        try:
            # Verify the verification code
            if not await self.verify_code(db, phone_number, verification_code, "phone_verification"):
                raise ValueError("Invalid verification code")

            # Check if phone is already linked to another user
            existing_user = db.query(UserDB).filter(
                UserDB.phone_number == phone_number,
                UserDB.id != user_id
            ).first()

            if existing_user:
                raise ValueError("Phone number is already linked to another user")

            # Update user
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            user.phone_number = phone_number
            user.phone_verified = True
            db.commit()

            logger.info(f"Linked phone number {phone_number} to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link phone to user: {str(e)}")
            raise

    async def update_password(self, db: Session, user_id: str, old_password: str, new_password: str) -> bool:
        """Update user password"""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            # For password reset via token, old_password may be empty
            # In that case, we skip the old password verification
            if old_password:
                # Verify old password
                if not self.secret_service.verify_user_password(db, user_id, old_password):
                    raise ValueError("Old password is incorrect")

            # Validate new password strength
            password_validation = self.password_service.validate_password_strength(new_password)
            if not password_validation.is_valid:
                raise ValueError(f"Password requirements not met: {password_validation.error}")

            # Hash new password
            crypto_keys = self.secret_service.get_user_crypto_keys(db, user_id)
            if not crypto_keys:
                raise ValueError("User crypto keys not found")

            hashed_password = self.password_service.hash_password(new_password, crypto_keys.salt)

            # Update password
            user.password_hash = hashed_password
            db.commit()

            logger.info(f"Updated password for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update password: {str(e)}")
            raise

    async def update_email(self, db: Session, user_id: str, new_email: str, verification_code: str) -> bool:
        """Update user email"""
        try:
            # Verify verification code (assuming it's sent to the new email)
            if not await self.verify_code(db, new_email, verification_code, "email_verification"):
                raise ValueError("Invalid verification code")

            # Check if email is already used by another user
            existing_user = db.query(UserDB).filter(
                UserDB.email == new_email,
                UserDB.id != user_id
            ).first()

            if existing_user:
                raise ValueError("Email is already in use by another user")

            # Update user
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            user.email = new_email
            db.commit()

            logger.info(f"Updated email for user {user_id} to {new_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to update email: {str(e)}")
            raise

    async def update_phone(self, db: Session, user_id: str, new_phone: str, verification_code: str) -> bool:
        """Update user phone number"""
        try:
            # Verify verification code
            if not await self.verify_code(db, new_phone, verification_code, "phone_verification"):
                raise ValueError("Invalid verification code")

            # Check if phone is already used by another user
            existing_user = db.query(UserDB).filter(
                UserDB.phone_number == new_phone,
                UserDB.id != user_id
            ).first()

            if existing_user:
                raise ValueError("Phone number is already in use by another user")

            # Update user
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            user.phone_number = new_phone
            user.phone_verified = True
            db.commit()

            logger.info(f"Updated phone number for user {user_id} to {new_phone}")
            return True

        except Exception as e:
            logger.error(f"Failed to update phone: {str(e)}")
            raise

    async def send_password_reset_email(self, db: Session, email: str) -> bool:
        """Send password reset email"""
        try:
            user = self.get_user_by_email(db, email)
            if not user:
                raise ValueError("User not found")

            # Generate password reset token
            token_data = {
                "user_id": user.id,
                "email": user.email or email,  # Use provided email if user.email is None
                "purpose": "password_reset"
            }
            reset_token = create_access_token(token_data, expires_minutes=15)

            # Send password reset email
            mail_service = MailService()
            success = mail_service.send_password_reset_email(user.email or email, reset_token, user.username)

            if success:
                logger.info(f"Password reset email sent successfully to {user.email or email}")
            else:
                logger.error(f"Failed to send password reset email to {user.email or email}")

            return success

        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            raise

    async def unlink_social_account(self, db: Session, user_id: str, provider: str) -> bool:
        """Unlink social account"""
        try:
            # Find the social account
            social_account = db.query(SocialAccountDB).filter(
                SocialAccountDB.user_id == user_id,
                SocialAccountDB.provider == provider
            ).first()

            if not social_account:
                raise ValueError("Social account not found")

            # Check if user has other login methods
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            # Prevent unlinking if this is the only login method
            has_other_login_methods = (
                user.password_hash or  # Has password
                user.phone_number or  # Has phone number
                db.query(SocialAccountDB).filter(
                    SocialAccountDB.user_id == user_id,
                    SocialAccountDB.provider != provider
                ).count() > 0  # Has other social accounts
            )

            if not has_other_login_methods:
                raise ValueError("Cannot unlink the only login method")

            # Remove social account
            db.delete(social_account)
            db.commit()

            logger.info(f"Unlinked {provider} account from user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unlink social account: {str(e)}")
            raise

    async def send_email_verification(self, db: Session, user_id: str) -> bool:
        """Send email verification link to user"""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            if not user.email:
                raise ValueError("User does not have an email address")

            if user.email_verified:
                raise ValueError("Email is already verified")

            # Generate verification token (valid for 24 hours)
            token_data = {
                "user_id": user.id,
                "email": user.email,
                "purpose": "email_verification"
            }
            verification_token = create_access_token(token_data, expires_minutes=1440)  # 24 hours

            # Send verification email
            mail_service = MailService()
            success = mail_service.send_email_verification(user.email, verification_token, user.username)

            if success:
                logger.info(f"Email verification sent successfully to {user.email}")
            else:
                logger.error(f"Failed to send email verification to {user.email}")

            return success

        except Exception as e:
            logger.error(f"Failed to send email verification: {str(e)}")
            raise

    async def verify_email(self, db: Session, token: str) -> bool:
        """Verify user's email using verification token"""
        try:
            from backend.middleware.auth import decode_access_token

            # Decode the token
            token_data = decode_access_token(token)
            if not token_data or token_data.get("purpose") != "email_verification":
                raise ValueError("Invalid or expired verification token")

            user_id = token_data.get("user_id")
            email = token_data.get("email")

            if not user_id or not email:
                raise ValueError("Invalid verification token")

            # Get user
            user = self.get_user_by_id(db, user_id)
            if not user:
                raise ValueError("User not found")

            # Verify that email matches
            if user.email != email:
                raise ValueError("Email mismatch")

            # Mark email as verified
            user.email_verified = True
            db.commit()

            logger.info(f"Email verified successfully for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to verify email: {str(e)}")
            raise
