import enum
from sqlalchemy import Column, String, Boolean, Enum
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class UserRole(str, enum.Enum):
    ASHA = "ASHA"
    ANM = "ANM"
    DOCTOR = "DOCTOR"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.ASHA)
    assigned_village_id = Column(String(100), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
