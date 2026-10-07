"""
backend/app/core/password_policy.py
Enterprise Password Policy Validator (W2 / W3).
Enforces minimum length, top common blacklist rejection, sequential pattern detection,
repeated character rejection, and user identifier separation.
"""

import re
from typing import Optional

# Comprehensive list of top common insecure passwords
TOP_COMMON_PASSWORDS = {
    "password", "12345678", "123456789", "1234567890", "qwerty123", "password123",
    "admin1234", "letmein123", "welcome123", "iloveyou123", "monkey123", "dragon123",
    "football123", "master123", "sunshine123", "princess123", "shadow123", "trustno1",
    "password1", "12345678a", "abcdefgh", "abcdef123", "passw0rd", "adminadmin",
    "testing123", "changeme", "default123", "secret123", "kalyan123", "hyderabad123",
    "telangana123", "ameerpet123", "bangalore123", "india123", "computer123", "root1234"
}

def is_sequential(s: str) -> bool:
    """Checks if string is a simple sequential sequence like 'abcdefgh' or '12345678'."""
    s_lower = s.lower()
    if len(s_lower) < 4:
        return False
    # Check ASCII forward sequence
    forward = all(ord(s_lower[i]) - ord(s_lower[i-1]) == 1 for i in range(1, len(s_lower)))
    # Check ASCII reverse sequence
    reverse = all(ord(s_lower[i-1]) - ord(s_lower[i]) == 1 for i in range(1, len(s_lower)))
    return forward or reverse

def is_all_same_char(s: str) -> bool:
    """Checks if string consists of only a single repeated character like 'aaaaaaaa'."""
    return len(s) > 0 and len(set(s)) == 1

def validate_password_strength(
    password: str,
    username: Optional[str] = None,
    email: Optional[str] = None
) -> str:
    """
    Validates password strength according to W2 acceptance criteria:
    - Min length 8
    - Max length 72 (bcrypt limit)
    - Not in common password blacklist
    - Not all same character
    - Not sequential pattern
    - Does not match username or email username
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
        
    if len(password.encode('utf-8')) > 72:
        raise ValueError("Password exceeds maximum length of 72 bytes (bcrypt restriction)")

    pwd_lower = password.lower().strip()

    if pwd_lower in TOP_COMMON_PASSWORDS:
        raise ValueError("Password is too common or easily guessable. Please choose a stronger password.")

    if is_all_same_char(password):
        raise ValueError("Password cannot consist of a single repeated character (e.g., 'aaaaaaaa')")

    if is_sequential(password):
        raise ValueError("Password cannot be a simple sequential pattern (e.g., 'abcdefgh', '12345678')")

    if username and len(username.strip()) >= 3:
        u_clean = username.lower().strip()
        if u_clean == pwd_lower or u_clean in pwd_lower:
            raise ValueError("Password cannot contain or match your username")

    if email and "@" in email:
        email_local = email.split("@")[0].lower().strip()
        if len(email_local) >= 3 and (email_local == pwd_lower or email_local in pwd_lower):
            raise ValueError("Password cannot contain your email prefix")

    return password
