from sqlalchemy import Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from helpers import uuidhex, _email, _username
from models.base import Base
from models.associations import user_roles


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    _id: Mapped[str] = mapped_column(Text, unique=True, default=uuidhex)
    username: Mapped[str] = mapped_column(String(32), default=_username)
    email: Mapped[str] = mapped_column(String(50), default=_email)
    password: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    secret: Mapped[str] = mapped_column(Text, nullable=True)
    token: Mapped[str] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    roles = relationship('Role', secondary=user_roles, back_populates='users', lazy='selectin')
    module_permissions = relationship('ModuleUser', back_populates='user', lazy='selectin', cascade='all, delete-orphan')

    def to_dict(self):
        return dict(
            _id=self._id,
            username=self.username,
            email=self.email,
            since=self.created_at.isoformat() if self.created_at else None,
            last_login=self.last_login.isoformat() if self.last_login else None,
            loggedin=self.status,
            verified=self.verified,
        )

    def __repr__(self):
        return f"{self.username} <{self.email}>"
