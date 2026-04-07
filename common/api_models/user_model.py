from pydantic import BaseModel, ConfigDict, validator
from datetime import datetime
from typing import Optional
from common.database_models.user_model import UserDB


class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    email: str
    password: str
    username: str


class PhoneLoginRequest(BaseModel):
    phone_number: str
    verification_code: str


class PhoneRegisterRequest(BaseModel):
    phone_number: str
    username: str
    verification_code: str
    password: Optional[str] = None  # Optional for phone-only users


class WeChatLoginRequest(BaseModel):
    code: str  # WeChat authorization code
    state: Optional[str] = None


class SendVerificationCodeRequest(BaseModel):
    phone_number: str
    type: str = "phone_verification"  # 'phone_verification', 'login', 'register'


class VerifyCodeRequest(BaseModel):
    phone_number: str
    code: str
    type: str = "phone_verification"


class UserResponse(BaseModel):
    email: Optional[str]
    username: str
    id: str
    exp_level: str = "1"
    phone_number: Optional[str]
    phone_verified: bool = False
    email_verified: bool = False
    wechat_nickname: Optional[str]
    wechat_avatar: Optional[str]
    created_at: datetime
    updated_at: datetime
    current_quota: Optional[dict] = None  # Include quota info

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class WeChatAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_new_user: bool


class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UpdateEmailRequest(BaseModel):
    new_email: str
    verification_code: str


class UpdatePhoneRequest(BaseModel):
    new_phone: str
    verification_code: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class SocialAccountResponse(BaseModel):
    provider: str
    account_id: str
    nickname: Optional[str]
    avatar: Optional[str]
    linked_at: datetime


class UserProfileResponse(UserResponse):
    email_verified: bool = False
    social_accounts: list[SocialAccountResponse] = []
