# Danloo Crypto Module

A shared cryptographic module for managing encryption keys and user authentication between backend and ai-provider services.

## Features

- **AK/SK Key Pair Management**: Generate and validate access/secret key pairs for API authentication
- **Password Hashing**: Secure password hashing using bcrypt with salt
- **Content Hashing**: HMAC-based content integrity verification
- **Bearer Token**: Create and validate JWT-like Bearer tokens for API access
- **Key Generation**: Cryptographically secure random key generation

## Installation

```bash
cd common
uv pip install -e .
```

For development:
```bash
uv pip install -e ".[dev]"
```

## Quick Start

```python
from crypto import (
    CryptoKeys,
    KeyGenerationService, 
    PasswordHashService,
    CryptoValidationService
)

# Generate keys for a user
key_pair = KeyGenerationService.generate_key_pair()
hash_key = KeyGenerationService.generate_hash_key()
salt = KeyGenerationService.generate_salt()

# Hash password
password = "SecurePassword123!"
hashed_password = PasswordHashService.hash_password(password, salt)

# Create user crypto keys
user_keys = CryptoKeys(
    user_id="user123",
    access_key=key_pair.access_key,
    secret_key=key_pair.secret_key,
    hash_key=hash_key,
    salt=salt,
    password_hash=hashed_password
)

# Validate and create tokens
validator = CryptoValidationService()
bearer_token = validator.create_bearer_token(
    key_pair.access_key,
    key_pair.secret_key
)
```

## Core Components

### 1. Key Generation Service

```python
from crypto.services.key_generation import KeyGenerationService
from crypto.types.crypto_types import KeyGenerationOptions, EncodingType

# Generate AK/SK pair
key_pair = KeyGenerationService.generate_key_pair()

# Custom options
options = KeyGenerationOptions(key_length=16, encoding=EncodingType.HEX)
custom_key_pair = KeyGenerationService.generate_key_pair(options)

# Generate hash key and salt
hash_key = KeyGenerationService.generate_hash_key()
salt = KeyGenerationService.generate_salt()
```

### 2. Password Hash Service

```python
from crypto.services.password_hash import PasswordHashService

# Hash password
hashed = PasswordHashService.hash_password(password, salt)

# Verify password
result = PasswordHashService.verify_password(password, hashed)

# Validate password strength
strength_result = PasswordHashService.validate_password_strength(password)
```

### 3. Crypto Validation Service

```python
from crypto.services.crypto_validation import CryptoValidationService

validator = CryptoValidationService()

# Validate AK/SK pair
result = validator.validate_ak_sk_pair(access_key, secret_key, stored_keys)

# Create Bearer token
token = validator.create_bearer_token(access_key, secret_key)

# Validate Bearer token
token_result = validator.validate_bearer_token(token, stored_keys)

# Content hashing
content_hash = validator.create_content_hash(content, hash_key)
hash_result = validator.validate_content_hash(content, hash_key, expected_hash)
```

## Usage in Backend Services

### Backend Service Integration

```python
# In your backend service
from crypto import CryptoKeys, KeyGenerationService, PasswordHashService

class UserService:
    def create_user(self, user_id: str, password: str) -> CryptoKeys:
        # Generate crypto keys
        key_pair = KeyGenerationService.generate_key_pair()
        hash_key = KeyGenerationService.generate_hash_key()
        salt = KeyGenerationService.generate_salt()
        
        # Hash password
        hashed_password = PasswordHashService.hash_password(password, salt)
        
        # Create and store crypto keys
        crypto_keys = CryptoKeys(
            user_id=user_id,
            access_key=key_pair.access_key,
            secret_key=key_pair.secret_key,
            hash_key=hash_key,
            salt=salt,
            password_hash=hashed_password
        )
        
        # Store in database (convert to dict)
        self.db.store_crypto_keys(crypto_keys.to_dict())
        
        return crypto_keys
    
    def authenticate_for_ai_provider(self, user_id: str) -> str:
        # Get user's crypto keys
        crypto_keys = self.get_user_crypto_keys(user_id)
        
        # Create Bearer token for ai-provider access
        validator = CryptoValidationService()
        return validator.create_bearer_token(
            crypto_keys.access_key,
            crypto_keys.secret_key
        )
```

### AI-Provider Service Integration

```python
# In your ai-provider service
from crypto import CryptoValidationService

class AuthMiddleware:
    def __init__(self):
        self.validator = CryptoValidationService()
    
    def authenticate_request(self, bearer_token: str, user_id: str) -> bool:
        # Get user's crypto keys from shared storage
        crypto_keys = self.get_user_crypto_keys(user_id)
        
        # Validate Bearer token
        result = self.validator.validate_bearer_token(bearer_token, crypto_keys)
        
        return result.is_valid
```

## Docker Integration

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy common crypto module
COPY ../common /app/common
RUN cd /app/common && uv pip install -e .

# Copy and install backend
COPY pyproject.toml .
RUN uv pip install -e .

COPY . .
CMD ["python", "main.py"]
```

### AI-Provider Dockerfile
```dockerfile
FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy common crypto module
COPY ../common /app/common
RUN cd /app/common && uv pip install -e .

# Copy and install ai-provider
COPY pyproject.toml .
RUN uv pip install -e .

COPY . .
CMD ["python", "main.py"]
```

## Testing

```bash
cd common
uv run pytest tests/
```

Run with coverage:
```bash
uv run pytest tests/ --cov=crypto --cov-report=html
```

## Security Considerations

1. **Key Storage**: Store secret keys encrypted at rest
2. **Transport**: Always use HTTPS/TLS for key transmission
3. **Key Rotation**: Implement periodic key rotation
4. **Token Expiration**: Configure appropriate token expiration times
5. **Password Strength**: Enforce strong password requirements

## Configuration

```python
from crypto.types.crypto_types import CryptoServiceConfig

config = CryptoServiceConfig(
    default_key_length=32,
    default_encoding=EncodingType.BASE64,
    bcrypt_rounds=12,
    token_expiration_ms=300000  # 5 minutes
)

validator = CryptoValidationService(config)
```

## Example Usage

See `example_usage.py` for a complete example demonstrating all features.

```bash
cd common
uv run python example_usage.py
```