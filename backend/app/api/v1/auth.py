import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.user import User, Profile, UserRole
from backend.app.schemas.auth import UserSignup, UserLogin, Token, UserProfile
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=Token)
def signup(data: UserSignup, db: Session = Depends(get_db)):
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
        personalization_enabled=True
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
    db.commit()

    token = create_access_token(data={"sub": user_id, "role": role.value})
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        username=new_user.username,
        role=role.value
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

    token = create_access_token(data={"sub": user.id, "role": user.role.value})
    return Token(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        username=user.username,
        role=user.role.value
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
        personalization_enabled=current_user.personalization_enabled
    )

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
