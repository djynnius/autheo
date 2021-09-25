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

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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


#onetime initialization
if __name__ == '__main__':
	#instantiate DB object
	dbo = DBO()

	Base.metadata.create_all(dbo.engine)

	admin = Role()
	admin.role = 'Admin'
	admin.description = 'The system administrator and superuser'

	registered = Role()
	registered.role = 'Registered User'
	registered.description = 'Registered user with login privileges'

	anon = Role()
	anon.role = 'Anonymous'
	anon.description = 'Anonymous login with no privileges'

	dbo.sess.add_all([admin, registered, anon])

	admin_role = UserRole()
	admin_role.user_id = 1
	admin_role.role_id = 1
	dbo.sess.add(admin_role)

	dbo.sess.commit()
