from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


class Module(Base):
    __tablename__ = 'modules'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module: Mapped[str] = mapped_column(String(75), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    user_permissions = relationship('ModuleUser', back_populates='module', lazy='selectin', cascade='all, delete-orphan')
    role_permissions = relationship('ModuleRole', back_populates='module', lazy='selectin', cascade='all, delete-orphan')

    def to_dict(self):
        return dict(
            id=self.id,
            module=self.module,
            description=self.description,
        )

    def __repr__(self):
        return f"{self.module}"
