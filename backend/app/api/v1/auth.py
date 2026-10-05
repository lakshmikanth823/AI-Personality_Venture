import uuid
import pyotp
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from backend.app.models.user import User, Profile, UserRole
from backend.app.models.safety import AuditLog
from backend.app.schemas.auth import (
    UserSignup, UserLogin, Token, UserProfile,
    MFASetupResponse, MFAVerifyRequest, ChangePasswordRequest
)
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(data: UserSignup, db: Session = Depends(get_db)):
    # 1. DPDP Act 2023 Consent Enforcement
    if not data.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Digital Personal Data Protection (DPDP) Act 2023 consent must be accepted to register."
        )

    # Check existing email or username
    existing_user = db.query(User).filter(
        (User.email == data.email) | (User.username == data.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists."
        )

    user_id = str(uuid.uuid4())
    # Create user (auto-grant admin to 'admin' username for operations)
    role = UserRole.ADMIN if data.username.lower() in ["admin", "operator"] else UserRole.USER

    new_user = User(
        id=user_id,
        email=data.email,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        role=role,
        is_active=True,
        personalization_enabled=True,
        must_change_password=False
    )
    db.add(new_user)
    db.flush()

    new_profile = Profile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        display_name=data.display_name or data.username,
        preferred_language=data.preferred_language or "hinglish"
    )
    db.add(new_profile)

    audit_consent = AuditLog(
        id=str(uuid.uuid4()),
        actor_id=user_id,
        actor_role="user",
        action="DPDP_CONSENT_CAPTURED",
        target_type="user",
        target_id=user_id,
        details_json='{"dpdp_act_version": "2023", "consent_type": "explicit_signup", "language": "hinglish"}'
    )
    db.add(audit_consent)
    db.commit()

    token = create_access_token(data={"sub": user_id, "role": role.value, "mfa_authenticated": True})
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        username=new_user.username,
        role=role.value,
        mfa_required=False,
        mfa_authenticated=True,
        must_change_password=False
    )

@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.email == data.email_or_username) | (User.username == data.email_or_username)
    ).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password."
        )

    # Check if MFA is active for this user
    is_mfa_authenticated = False
    mfa_required = user.mfa_enabled or (user.role in [UserRole.ADMIN, UserRole.OPERATOR])

    if user.mfa_enabled:
        if data.totp_code:
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(data.totp_code, valid_window=1):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid TOTP MFA verification code."
                )
            is_mfa_authenticated = True
        else:
            # Issue partial session token requiring MFA challenge completion
            is_mfa_authenticated = False
    else:
        # Standard user without MFA configured
        is_mfa_authenticated = True

    token = create_access_token(data={
        "sub": user.id,
        "role": user.role.value,
        "mfa_authenticated": is_mfa_authenticated
    })

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        mfa_required=mfa_required and not is_mfa_authenticated,
        mfa_authenticated=is_mfa_authenticated,
        must_change_password=user.must_change_password
    )

@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role.value,
        display_name=current_user.profile.display_name if current_user.profile else current_user.username,
        preferred_language=current_user.profile.preferred_language if current_user.profile else "hinglish",
        personalization_enabled=current_user.personalization_enabled,
        mfa_enabled=current_user.mfa_enabled,
        must_change_password=current_user.must_change_password
    )

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed."
        )
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long."
        )

    current_user.hashed_password = get_password_hash(data.new_password)
    current_user.must_change_password = False
    db.commit()
    return {"status": "success", "message": "Password changed successfully."}

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    secret = pyotp.random_base32()
    current_user.mfa_secret = secret
    db.commit()

    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=current_user.email, issuer_name="Kalyan AI")
    return MFASetupResponse(
        secret=secret,
        otpauth_url=otpauth_url,
        qr_code_hint=f"Add secret '{secret}' to your TOTP Authenticator (Google Authenticator, Authy, 1Password)"
    )

@router.post("/mfa/verify", response_model=Token)
def verify_mfa(
    data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA setup has not been initiated. Call /auth/mfa/setup first."
        )

    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP verification code. Ensure your device clock is synchronized."
        )

    current_user.mfa_enabled = True
    db.commit()

    token = create_access_token(data={
        "sub": current_user.id,
        "role": current_user.role.value,
        "mfa_authenticated": True
    })

    return Token(
        access_token=token,
        token_type="bearer",
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        mfa_required=False,
        mfa_authenticated=True,
        must_change_password=current_user.must_change_password
    )

@router.get("/mfa/status")
def mfa_status(current_user: User = Depends(get_current_user)):
    return {
        "mfa_enabled": current_user.mfa_enabled,
        "mfa_required": current_user.role in [UserRole.ADMIN, UserRole.OPERATOR]
    }

@router.post("/privacy/toggle-personalization")
def toggle_personalization(
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.personalization_enabled = enabled
    db.commit()
    return {
        "status": "success",
        "personalization_enabled": current_user.personalization_enabled,
        "message": f"Personalization has been {'enabled' if enabled else 'disabled'}. Memory retrieval and storage will reflect this preference."
    }
