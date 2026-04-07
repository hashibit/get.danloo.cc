from pydantic import BaseModel, ConfigDict
from datetime import datetime
from common.database_models.crypto_keys_model import CryptoKeysDB


class CryptoKeysCreate(BaseModel):
    """Model for creating crypto keys"""

    user_id: str


class CryptoKeysResponse(BaseModel):
    """Model for crypto keys response (without sensitive data)"""

    user_id: str
    access_key: str  # Only AK is exposed, SK is kept secret
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
