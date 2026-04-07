#!/usr/bin/env python3
"""
Example usage of the crypto module.
"""

from crypto import (
    CryptoKeys,
    KeyGenerationService,
    PasswordHashService,
    CryptoValidationService,
)
from crypto.types.crypto_types import KeyGenerationOptions, EncodingType


def main():
    print("=== Danloo Crypto Module Example ===\n")

    # 1. Generate crypto keys for a user
    print("1. Generating crypto keys...")
    key_pair = KeyGenerationService.generate_key_pair()
    hash_key = KeyGenerationService.generate_hash_key()
    salt = KeyGenerationService.generate_salt()

    print(f"   Access Key: {key_pair.access_key[:20]}...")
    print(f"   Secret Key: {key_pair.secret_key[:20]}...")
    print(f"   Hash Key: {hash_key[:20]}...")
    print(f"   Salt: {salt[:20]}...")

    # 2. Hash a password
    print("\n2. Hashing password...")
    password = "MySecurePass123!"

    # Validate password strength first
    validation_result = PasswordHashService.validate_password_strength(password)
    if validation_result.is_valid:
        print("   Password strength: VALID")

        hashed_password = PasswordHashService.hash_password(password, salt)
        print(f"   Hashed password: {hashed_password[:30]}...")
    else:
        print(f"   Password strength: INVALID - {validation_result.error}")
        return

    # 3. Create CryptoKeys object
    print("\n3. Creating CryptoKeys object...")
    crypto_keys = CryptoKeys(
        user_id="user_12345",
        access_key=key_pair.access_key,
        secret_key=key_pair.secret_key,
        hash_key=hash_key,
        salt=salt,
        password_hash=hashed_password,
    )
    print(f"   Created keys for user: {crypto_keys.user_id}")

    # 4. Validate AK/SK pair
    print("\n4. Validating AK/SK pair...")
    validator = CryptoValidationService()
    ak_sk_result = validator.validate_ak_sk_pair(
        key_pair.access_key, key_pair.secret_key, crypto_keys
    )
    print(f"   AK/SK validation: {'VALID' if ak_sk_result.is_valid else 'INVALID'}")

    # 5. Create and validate Bearer token
    print("\n5. Creating Bearer token...")
    bearer_token = validator.create_bearer_token(
        key_pair.access_key, key_pair.secret_key
    )
    print(f"   Bearer token: {bearer_token[:50]}...")

    print("\n6. Validating Bearer token...")
    token_result = validator.validate_bearer_token(bearer_token, crypto_keys)
    print(f"   Token validation: {'VALID' if token_result.is_valid else 'INVALID'}")

    # 7. Create content hash
    print("\n7. Creating content hash...")
    content = "This is important content that needs to be verified"
    content_hash = validator.create_content_hash(content, hash_key)
    print(f"   Content: {content}")
    print(f"   Hash: {content_hash}")

    # 8. Validate content hash
    print("\n8. Validating content hash...")
    hash_result = validator.validate_content_hash(content, hash_key, content_hash)
    print(f"   Hash validation: {'VALID' if hash_result.is_valid else 'INVALID'}")

    # 9. Verify password
    print("\n9. Verifying password...")
    password_result = PasswordHashService.verify_password(password, hashed_password)
    print(
        f"   Password verification: {'VALID' if password_result.is_valid else 'INVALID'}"
    )

    # 10. Convert to/from dict (for storage)
    print("\n10. Converting to dictionary (for database storage)...")
    keys_dict = crypto_keys.to_dict()
    print("   Keys converted to dict format for storage")

    restored_keys = CryptoKeys.from_dict(keys_dict)
    print(f"   Restored keys for user: {restored_keys.user_id}")

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()
