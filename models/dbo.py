from sqlalchemy import (
	create_engine, 
	Table, 
	Column, 
	Integer, 
	Float,
	String, 
	Text, 
	Date, 
	DateTime, 
	Boolean, 
	ForeignKey
)

from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from urllib import parse
from datetime import datetime
from uuid import uuid4 as uuid
from helpers import _email, _username, uuidhex

Base = declarative_base()

class DBO():
	def __init__(self, sqlite_path='autheo.db'):
		dsn = 'sqlite:///{sqlite_path}'.format(sqlite_path=sqlite_path)
		#config = {'conn':'mysql', 'user':'root', 'pswd':parse.quote('pswd'), 'host':'127.0.0.1', 'port':'3360', 'name':'autheo')
		#dsn = '''{conn}://{user}:{pswd}@{host}:{port}/{name}'''.format(config)
		self.engine = create_engine(dsn)
		
		session = sessionmaker(bind=self.engine)
		self.sess = session()

UserRole = Table(
	'users_roles', 
	Base.metadata, 
	Column('user_id', Integer, ForeignKey('users.id')), 
	Column('role_id', Integer, ForeignKey('roles.id'))
)

ModuleUser = Table(
	'modules_users', 
	Base.metadata,
	Column('module_id', Integer, ForeignKey('modules.id')),
	Column('user_id', Integer, ForeignKey('users.id')),
	Column('permissions', Integer) #use Unix convention read=1, write=2, execute=4
)

ModuleRole = Table(
	'modules_roles', 
	Base.metadata, 
	Column('module_id', Integer, ForeignKey('modules.id')),
	Column('role_id', Integer, ForeignKey('roles.id')),
	Column('permissions', Integer) #use Unix convention read=1, write=2, execute=4
)


class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	_id = Column(Text, unique=True, default=uuidhex)
	username = Column(String(32), default=_username)
	email = Column(String(50), default=_email)
	password = Column(Text)
	status = Column(Boolean, default=False)
	created_at = Column(DateTime, default=datetime.now())
	last_login = Column(DateTime, default=datetime.now())
	secret = Column(Text)
	token = Column(Text)
	verified = Column(Boolean, default=False)
	roles = relationship('Role', secondary=UserRole, back_populates='users')
	modules = relationship('Module', secondary=ModuleUser, back_populates='users')

	def __repr__(self):
		return f"{self.username} <{self.email}>"

class Role(Base):
	__tablename__ = 'roles'
	id = Column(Integer, primary_key=True)
	role = Column(String(75), unique=True)
	description = Column(Text)
	users = relationship('User', secondary=UserRole, back_populates='roles')
	modules = relationship('Module', secondary=ModuleRole, back_populates='roles')

	def __repr__(self):
		return f"{self.role}"

class Module(Base):
	__tablename__ = 'modules'
	id = Column(Integer, primary_key=True)
	module = Column(String(75), unique=True)
	description = Column(Text)
	users = relationship('User', secondary=ModuleUser, back_populates='modules')
	roles = relationship('Role', secondary=ModuleRole, back_populates='modules')

	def __repr__(self):
		return f"{self.module}"


#onetime initialization
if __name__ == '__main__':
	#instantiate DB object
	dbo = DBO()

	Base.metadata.create_all(dbo.engine)

	#Create Admin role
	admin = Role()
	admin.role = 'administrator'
	admin.description = 'The system administrator and superuser'

	#Create Registered Role
	registered = Role()
	registered.role = 'registered'
	registered.description = 'Registered user with login privileges'

	#Create Anonymous role for visitors
	anon = Role()
	anon.role = 'anonymous'
	anon.description = 'Anonymous login with no privileges'

	#Add all roles
	dbo.sess.add_all([admin, registered, anon])


	#Commit all changes
	dbo.sess.commit()
