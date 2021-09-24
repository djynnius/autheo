from sqlalchemy import (
	create_engine, 
	Table, 
	Column, 
	Integer, 
	Float,
	String, 
	Text, 
	Date, 
	Datetime, 
	Boolean, 
	ForeignKey
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib import parse

Base = declarative_base()

class DBO():
	def __init__(self):
		adapter = 'sqlite:///autheo.db'
		#adapter = '''mysql+pymysql://{user}:{pswd}@{host}:{port}/{name}'''.format(user='root', pswd=parse.quote('pswd'), host='127.0.0.1', port='3360', name='autheo')
		
		self.engine = create_engine(adapter)
		
		session = sessionmaker(bind=self.engine)
		self.sess = session()

class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	username = Column(String(32))
	email = Column(String(50))
	password = Column(Text)
	status = Column(Boolean, default=False)
	created_at = Column(DateTime)
	last_login = Column(DateTime)

class Role(Base):
	__tablename__ = 'roles'
	id = Column(Integer, primary_key=True)
	role = Column(String(75), unique=True)
	description = Column(Text)


#onetime initialization
if __name__ == '__main__':
	dbo = DBO()

	roles = [role for role in dbo.engine.execute('SELECT * FROM roles').fetchall()]

	if len(roles) == 0:

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