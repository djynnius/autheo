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

from sqlalchemy.orm import sessionmaker, declarative_base
from urllib import parse
from datetime import datetime

Base = declarative_base()

class DBO():
	def __init__(self, sqlite_path='autheo.db'):
		dsn = 'sqlite:///{sqlite_path}'.format(sqlite_path=sqlite_path)
		#config = {'conn':'mysql', 'user':'root', 'pswd':parse.quote('pswd'), 'host':'127.0.0.1', 'port':'3360', 'name':'autheo')
		#dsn = '''{conn}://{user}:{pswd}@{host}:{port}/{name}'''.format(config)
		self.engine = create_engine(dsn)
		
		session = sessionmaker(bind=self.engine)
		self.sess = session()

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	_id = Column(Text, unique=True)
	username = Column(String(32))
	email = Column(String(50))
	password = Column(Text)
	status = Column(Boolean, default=False)
	created_at = Column(DateTime, default=datetime.now())
	last_login = Column(DateTime, default=datetime.now())
	secret = Column(Text)
	token = Column(Text)
	verified = Column(Boolean, default=False)

class Role(Base):
	__tablename__ = 'roles'
	id = Column(Integer, primary_key=True)
	role = Column(String(75), unique=True)
	description = Column(Text)

class UserRole(Base):
	__tablename__ = 'users_roles'
	id = Column(Integer, primary_key=True)
	user_id = Column(Integer, ForeignKey('users.id'))
	role_id = Column(Integer, ForeignKey('roles.id'))

class Module(Base):
	__tablename__ = 'modules'
	id = Column(Integer, primary_key=True)
	module = Column(String(75), unique=True)
	description = Column(Text)

class ModuleRole(Base):
	__tablename__ = 'modules_roles'
	id = Column(Integer, primary_key=True)
	module_id = Column(Integer, ForeignKey('modules.id'))
	role_id = Column(Integer, ForeignKey('roles.id'))
	permissions = Column(Integer) #use Unix convention read=1, write=2, execute=4

class ModuleUser(Base):
	__tablename__ = 'modules_users'
	id = Column(Integer, primary_key=True)
	module_id = Column(Integer, ForeignKey('modules.id'))
	user_id = Column(Integer, ForeignKey('roles.id'))
	permissions = Column(Integer) #use Unix convention read=1, write=2, execute=4


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
