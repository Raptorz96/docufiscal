"""Authentication endpoints for user registration, login, and profile."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserUpdate, PasswordChange

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new user account.

    Args:
        user_data: User registration data
        db: Database session dependency

    Returns:
        UserResponse: Created user data

    Raises:
        HTTPException: 409 if email already exists
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = hash_password(user_data.password)

    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        nome=user_data.nome,
        cognome=user_data.cognome,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return UserResponse.model_validate(db_user)


@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticate user and return access token.

    Args:
        form_data: OAuth2 form data (username=email, password)
        db: Database session dependency

    Returns:
        Token: JWT access token and type

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Query user by email (OAuth2 uses username field for email)
    user = db.query(User).filter(User.email == form_data.username).first()

    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
        )

    # Create access token
    access_token = create_access_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Args:
        current_user: Current authenticated user dependency

    Returns:
        UserResponse: Current user profile data
    """
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile (nome, cognome, email).
    Only non-None fields are applied. Email change is allowed but will
    invalidate the current JWT token (sub = email).
    """
    # No-op if nothing provided (exclude_unset=True checks what was actually sent)
    if not user_data.model_dump(exclude_unset=True):
        return UserResponse.model_validate(current_user)

    # Check email uniqueness
    if user_data.email is not None and user_data.email != current_user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email già in uso da un altro account",
            )

    # Apply updates
    if user_data.nome is not None:
        current_user.nome = user_data.nome
    if user_data.cognome is not None:
        current_user.cognome = user_data.cognome
    if user_data.email is not None:
        current_user.email = user_data.email

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Change current user's password.
    Verifies current password, enforces min length of 8, then saves new hash.
    Does NOT invalidate existing JWT tokens.
    """
    # Validate new password first (cheap) before the expensive bcrypt comparison
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password deve essere di almeno 8 caratteri",
        )

    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password corrente non corretta",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    return {"detail": "Password aggiornata con successo"}
