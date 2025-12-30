import re
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator

from ..db import get_db
from ..models import User, Tenant
from ..auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

# Pydantic schemas
class UserBase(BaseModel):
    email: EmailStr
    role: str = "employee"
    whatsapp_number: str | None = Field(None, description="E.164 format: +54911...")
    whatsapp_wa_id: str | None = Field(None, description="WhatsApp ID: digits only 54911...")

    @field_validator("whatsapp_number")
    @classmethod
    def validate_whatsapp_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # E.164: + followed by 1-15 digits
        if not re.match(r"^\+[0-9]{1,15}$", v):
            raise ValueError("whatsapp_number must be E.164 format: +54911...")
        return v

    @field_validator("whatsapp_wa_id")
    @classmethod
    def validate_whatsapp_wa_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Only digits, 10-15 chars
        if not re.match(r"^[0-9]{10,15}$", v):
            raise ValueError("whatsapp_wa_id must be digits only (10-15 chars)")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = ["owner", "admin", "employee", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"role must be one of {valid_roles}")
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    role: str | None = None
    whatsapp_number: str | None = None
    whatsapp_wa_id: str | None = None

    @field_validator("whatsapp_number")
    @classmethod
    def validate_whatsapp_number(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\+[0-9]{1,15}$", v):
            raise ValueError("whatsapp_number must be E.164 format: +54911...")
        return v

    @field_validator("whatsapp_wa_id")
    @classmethod
    def validate_whatsapp_wa_id(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^[0-9]{10,15}$", v):
            raise ValueError("whatsapp_wa_id must be digits only (10-15 chars)")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_roles = ["owner", "admin", "employee", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"role must be one of {valid_roles}")
        return v


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    email: str
    role: str
    is_active: bool
    whatsapp_number: str | None
    whatsapp_wa_id: str | None

    class Config:
        from_attributes = True


# Helpers
def _check_admin_or_owner(user: User) -> None:
    """Verificar que el usuario sea admin u owner."""
    if user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Only admin/owner can manage users")

def _get_current_user_from_db(db: Session, auth_token: dict) -> User:
    """Obtener usuario desde la BD usando datos del token."""
    user_id = auth_token.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


# Endpoints
@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    auth_token: dict = Depends(get_current_user),
):
    """Listar usuarios del tenant (admin/owner only)."""
    current_user = _get_current_user_from_db(db, auth_token)
    _check_admin_or_owner(current_user)
    users = db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
    return users


@router.post("", response_model=UserResponse)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    auth_token: dict = Depends(get_current_user),
):
    """Crear nuevo usuario (admin/owner only)."""
    current_user = _get_current_user_from_db(db, auth_token)
    _check_admin_or_owner(current_user)

    # Verificar email único globalmente
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Verificar whatsapp_wa_id único por tenant
    if body.whatsapp_wa_id:
        if db.query(User).filter(
            User.tenant_id == current_user.tenant_id,
            User.whatsapp_wa_id == body.whatsapp_wa_id,
        ).first():
            raise HTTPException(status_code=400, detail="whatsapp_wa_id already in use for this tenant")

    # Verificar whatsapp_number único por tenant
    if body.whatsapp_number:
        if db.query(User).filter(
            User.tenant_id == current_user.tenant_id,
            User.whatsapp_number == body.whatsapp_number,
        ).first():
            raise HTTPException(status_code=400, detail="whatsapp_number already in use for this tenant")

    # Hash password (simplificado; usa bcrypt en prod)
    password_hash = f"hashed_{body.password}"  # TODO: usar bcrypt

    user = User(
        tenant_id=current_user.tenant_id,
        email=body.email,
        password_hash=password_hash,
        role=body.role,
        whatsapp_number=body.whatsapp_number,
        whatsapp_wa_id=body.whatsapp_wa_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"✅ Created user: {user.email} (id={user.id}, wa_id={user.whatsapp_wa_id})")
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    auth_token: dict = Depends(get_current_user),
):
    """Obtener usuario por ID (mismo tenant)."""
    current_user = _get_current_user_from_db(db, auth_token)
    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    auth_token: dict = Depends(get_current_user),
):
    """Actualizar usuario (admin/owner only)."""
    current_user = _get_current_user_from_db(db, auth_token)
    _check_admin_or_owner(current_user)

    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verificar unicidad de whatsapp_wa_id
    if body.whatsapp_wa_id and body.whatsapp_wa_id != user.whatsapp_wa_id:
        if db.query(User).filter(
            User.tenant_id == current_user.tenant_id,
            User.whatsapp_wa_id == body.whatsapp_wa_id,
            User.id != user_id,
        ).first():
            raise HTTPException(status_code=400, detail="whatsapp_wa_id already in use for this tenant")

    # Verificar unicidad de whatsapp_number
    if body.whatsapp_number and body.whatsapp_number != user.whatsapp_number:
        if db.query(User).filter(
            User.tenant_id == current_user.tenant_id,
            User.whatsapp_number == body.whatsapp_number,
            User.id != user_id,
        ).first():
            raise HTTPException(status_code=400, detail="whatsapp_number already in use for this tenant")

    # Actualizar campos
    if body.role:
        user.role = body.role
    if body.whatsapp_number is not None:
        user.whatsapp_number = body.whatsapp_number
    if body.whatsapp_wa_id is not None:
        user.whatsapp_wa_id = body.whatsapp_wa_id

    db.commit()
    db.refresh(user)
    logger.info(f"✅ Updated user: {user.email} (id={user.id})")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    auth_token: dict = Depends(get_current_user),
):
    """Desactivar usuario (admin/owner only)."""
    current_user = _get_current_user_from_db(db, auth_token)
    _check_admin_or_owner(current_user)

    user = db.query(User).filter(User.id == user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Marcar como inactivo en lugar de borrar
    user.is_active = False
    db.commit()
    logger.info(f"✅ Deactivated user: {user.email} (id={user.id})")
    return {"status": "deactivated", "user_id": user.id}
