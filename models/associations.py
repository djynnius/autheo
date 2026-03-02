from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base


# Pure junction table (no extra columns) - stays as Table
user_roles = Table(
    'users_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
)


class ModuleUser(Base):
    """Module-User permission association - mapped ORM class for instantiation and querying."""
    __tablename__ = 'modules_users'

    module_id: Mapped[int] = mapped_column(
        ForeignKey('modules.id', ondelete='CASCADE'), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    permissions: Mapped[int] = mapped_column(Integer, default=0)

    module = relationship('Module', back_populates='user_permissions')
    user = relationship('User', back_populates='module_permissions')


class ModuleRole(Base):
    """Module-Role permission association - mapped ORM class for instantiation and querying."""
    __tablename__ = 'modules_roles'

    module_id: Mapped[int] = mapped_column(
        ForeignKey('modules.id', ondelete='CASCADE'), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True
    )
    permissions: Mapped[int] = mapped_column(Integer, default=0)

    module = relationship('Module', back_populates='role_permissions')
    role = relationship('Role', back_populates='module_permissions')
