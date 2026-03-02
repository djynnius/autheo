from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from models.associations import user_roles


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(75), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    users = relationship('User', secondary=user_roles, back_populates='roles', lazy='selectin')
    module_permissions = relationship('ModuleRole', back_populates='role', lazy='selectin', cascade='all, delete-orphan')

    def to_dict(self):
        return dict(
            id=self.id,
            role=self.role,
            description=self.description,
        )

    def __repr__(self):
        return f"{self.role}"
