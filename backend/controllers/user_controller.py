from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from common.api_models.user_model import (
    UserCreate, UserLogin, UserResponse,
    PhoneLoginRequest, PhoneRegisterRequest, WeChatLoginRequest,
    SendVerificationCodeRequest, VerifyCodeRequest,
    AuthResponse, WeChatAuthResponse, UpdatePasswordRequest,
    UpdateEmailRequest, UpdatePhoneRequest, ForgotPasswordRequest,
    UserProfileResponse, ResetPasswordRequest
)
from common.api_models.crypto_keys_model import CryptoKeysResponse


class EmailVerificationRequest(BaseModel):
    token: str


from backend.services.user_service import UserService
from backend.middleware.auth import get_current_user
from backend.database import get_database
from sqlalchemy.orm import Session

router = APIRouter()

# Initialize user service
user_service = UserService()


@router.post(
    "/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user: UserCreate, db: Session = Depends(get_database)):
    """Register a new user and automatically login"""
    try:
        new_user = user_service.create_user(db, user)
        
        # Create access token for automatic login
        from backend.middleware.auth import create_access_token
        token_data = {
            "user_id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
        }
        access_token = create_access_token(token_data)
        
        # Convert user to response format
        from common.database_models.user_model import UserDB
        user_response = UserResponse.model_validate(new_user)
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(user: UserLogin, db: Session = Depends(get_database)):
    """Login user and return access token"""
    try:
        token = user_service.authenticate_user(db, user.email, user.password)
        if token:
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_database)
):
    """Get current user profile with quota information"""
    try:
        user_with_quota = user_service.get_user_with_quota(db, current_user["user_id"])
        if user_with_quota:
            return user_with_quota
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me/crypto-keys", response_model=CryptoKeysResponse)
async def get_user_crypto_keys(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_database)
):
    """Get current user's crypto keys (AK only, SK is kept secret)"""
    try:
        crypto_keys = user_service.get_user_crypto_keys(db, current_user["user_id"])
        if crypto_keys:
            return crypto_keys
        else:
            raise HTTPException(status_code=404, detail="Crypto keys not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/rotate-keys")
async def rotate_user_crypto_keys(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_database)
):
    """Rotate user's crypto keys (generate new AK/SK pair)"""
    try:
        crypto_keys = user_service.rotate_user_crypto_keys(db, current_user["user_id"])
        return {
            "message": "Crypto keys rotated successfully",
            "access_key": crypto_keys.access_key,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Phone verification endpoints
@router.post("/send-verification-code", status_code=status.HTTP_200_OK)
async def send_verification_code(
    request: SendVerificationCodeRequest, db: Session = Depends(get_database)
):
    """Send verification code to phone number"""
    try:
        result = await user_service.send_verification_code(db, request.phone_number, request.type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-code", status_code=status.HTTP_200_OK)
async def verify_code(
    request: VerifyCodeRequest, db: Session = Depends(get_database)
):
    """Verify verification code"""
    try:
        result = await user_service.verify_code(db, request.phone_number, request.code, request.type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Phone registration and login endpoints
@router.post(
    "/register-phone", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user_with_phone(
    user: PhoneRegisterRequest, db: Session = Depends(get_database)
):
    """Register a new user with phone number"""
    try:
        new_user = await user_service.create_user_with_phone(db, user)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login-phone", status_code=status.HTTP_200_OK)
async def login_user_with_phone(
    request: PhoneLoginRequest, db: Session = Depends(get_database)
):
    """Login user with phone number and verification code"""
    try:
        token = await user_service.authenticate_user_with_phone(
            db, request.phone_number, request.verification_code
        )
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# WeChat login endpoint
@router.post("/login-wechat", response_model=WeChatAuthResponse, status_code=status.HTTP_200_OK)
async def login_user_with_wechat(
    request: WeChatLoginRequest, db: Session = Depends(get_database)
):
    """Login user with WeChat"""
    try:
        result = await user_service.authenticate_with_wechat(db, request)
        return {
            "access_token": result["access_token"],
            "token_type": "bearer",
            "user": result["user"],
            "is_new_user": result["is_new_user"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# WeChat authorization URL endpoint
@router.get("/wechat-auth-url", status_code=status.HTTP_200_OK)
async def get_wechat_auth_url(redirect_uri: str, state: str = None):
    """Get WeChat authorization URL"""
    try:
        from backend.services.wechat_service import get_wechat_service
        wechat_service = get_wechat_service()
        auth_url = wechat_service.generate_auth_url(state, "snsapi_login")
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Link phone to existing user
@router.post("/me/link-phone", status_code=status.HTTP_200_OK)
async def link_phone_to_user(
    phone_number: str,
    verification_code: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Link phone number to existing user"""
    try:
        success = await user_service.link_phone_to_user(
            db, current_user["user_id"], phone_number, verification_code
        )
        if success:
            return {"message": "Phone number linked successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to link phone number")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Profile management endpoints
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_database)
):
    """Get current user profile with detailed information"""
    try:
        user = user_service.get_user_profile_with_social_accounts(db, current_user["user_id"])
        if user:
            return user
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def update_password(
    request: UpdatePasswordRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Update user password"""
    try:
        success = await user_service.update_password(
            db, current_user["user_id"], request.old_password, request.new_password
        )
        if success:
            return {"message": "Password updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update password")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/me/email", status_code=status.HTTP_200_OK)
async def update_email(
    request: UpdateEmailRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Update user email"""
    try:
        success = await user_service.update_email(
            db, current_user["user_id"], request.new_email, request.verification_code
        )
        if success:
            return {"message": "Email updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update email")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/me/phone", status_code=status.HTTP_200_OK)
async def update_phone(
    request: UpdatePhoneRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Update user phone number"""
    try:
        success = await user_service.update_phone(
            db, current_user["user_id"], request.new_phone, request.verification_code
        )
        if success:
            return {"message": "Phone number updated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update phone")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_database)
):
    """Send password reset email"""
    try:
        success = await user_service.send_password_reset_email(db, request.email)
        if success:
            return {"message": "Password reset email sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send password reset email")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_database)
):
    """Reset user password using token"""
    try:
        # Decode the token to get user information
        from backend.middleware.auth import decode_access_token
        token_data = decode_access_token(request.token)

        if not token_data or token_data.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")

        user_id = token_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid reset token")

        # Validate password strength
        from common.crypto.services.password_hash import PasswordHashService
        password_validation = PasswordHashService.validate_password_strength(request.new_password)
        if not password_validation.is_valid:
            raise HTTPException(status_code=400, detail=password_validation.error)

        # Update user password
        success = await user_service.update_password(db, user_id, "", request.new_password)
        if success:
            return {"message": "Password reset successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to reset password")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Password reset failed: {str(e)}")


@router.delete("/me/social/{provider}", status_code=status.HTTP_200_OK)
async def unlink_social_account(
    provider: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Unlink social account"""
    try:
        success = await user_service.unlink_social_account(db, current_user["user_id"], provider)
        if success:
            return {"message": "Social account unlinked successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to unlink social account")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/send-email-verification", status_code=status.HTTP_200_OK)
async def send_email_verification(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """Send email verification link to current user"""
    try:
        success = await user_service.send_email_verification(db, current_user["user_id"])
        if success:
            return {"message": "Email verification link sent successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to send email verification")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_database)
):
    """Verify user's email using verification token from request body"""
    try:
        success = await user_service.verify_email(db, request.token)
        if success:
            return {"message": "Email verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to verify email")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
