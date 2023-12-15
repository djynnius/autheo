from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
from sqlalchemy import text, or_, and_, not_
from sqlalchemy.orm import Session
import re
import jwt
from bcrypt import hashpw, checkpw, gensalt
from hashlib import md5
from datetime import datetime, timedelta
from models.dbo import *


ent = Blueprint('authentication', __name__, url_prefix='/ent')
sqlite_path = ent.root_path.replace('controllers', 'dbs/autheo.db')
dbo = DBO(sqlite_path)

'''
Signup with email or username or both
'''
@ent.route("/signup", methods=['POST'])
@cross_origin()
def signup():
	keys = [item for item in req.form]

	#expects password to be included in request
	if 'password' not in keys:
		return jsonify(dict(status='error', msg='no password'))

	#expects one or more of username or email
	if 'email' not in keys and 'username' not in keys:
		return jsonify(dict(status='error', message='no username or email'))

	#remove whitespace from edges of form inputs
	username = req.form.get('username', '').strip()
	email = req.form.get('email', '').strip()
	password = req.form.get('password', '').strip()

	if username == '' and email == '':
		return jsonify(dict(status='error', message='You must add at least one of email or username'))

	#username validator
	if username != '':
		#username must be at least 8 characters in length and 
		if len(username) < 8:
			return jsonify(dict(status='error', message='username is less than 8 characters long'))
		#can contain only lettres, number, underscores and dots
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9_]+)$', username) == None:
			return jsonify(dict(status='error', message='username can only contain numbers and letters, underscore and dot. username cannot start with a number, underscore or dor nor can it end with a dot or underscore'))

	#email validator
	if email != '':
		#username must be at least 8 characters in length and 
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9]+)@([a-zA-Z]+).([a-zA-Z.]{2,5})$', email) == None:
			return jsonify(dict(status='error', message='this is not a valid email'))

	if password != '':
		#username must be at least 8 characters in length and 
		if len(password) < 8:
			return jsonify(dict(status='error', message='password is less than 8 characters long'))
		#password must contain lowecase, uppercase, number and special character and 
		if re.search(r'[a-z]+', password) == None or re.search(r'[A-Z]+', password) == None or re.search(r'[0-9]+', password) == None or re.search(r'[_.$@*!+#%&-]+', password) == None: 
			return jsonify(dict(status='error', message='password must contain lowercase, uppercase, number and special character'))

	#convert username and email to all lowercase since not case sensitive
	username = username.lower()
	email = email.lower()

	#check if the user exists
	with dbo.engine.connect() as con:
		people = con.execute(text(f"SELECT id FROM users WHERE (username='{username}' AND username IS NOT NULL) OR (email='{email}' AND email IS NOT NULL)")).fetchall()
		if len(people) > 0:
			return jsonify(dict(status='error', message='a user with these credentials already exists'))
	

	#instantiate user object

	user = User()
	if username != '': user.username = username
	if email != '': user.email = email
	user.password = hashpw(password.encode(), gensalt()) #encrypt password
	user.secret = hashpw(str(datetime.now()).encode(), gensalt())[2:32] #make user unique secret for JWT
	user.token = init_token(user) #set initial JWT token which is already expired
	dbo.sess.add(user)
	dbo.sess.commit()

	with Session(dbo.engine) as sess:
		#set a unique identifier hash
		with dbo.engine.connect() as con:
			person = con.execute(
				text(f'''	SELECT * 
					FROM users 
					WHERE username='{username}' OR email='{email}'
				''')
			).fetchone()

		user = sess.query(User).filter_by(id=person.id).one()
		#create hash version of id
		_id = md5(f"{person.id}_{person.created_at}".encode()).hexdigest()
		user._id = _id

		#if first user make admin
		if user.id == 1:
			admin = UserRole()
			admin.user_id = 1
			admin.role_id = 1
			sess.add(admin)

		#add all signed up people into the registered role
		ur = UserRole()
		ur.role_id = 2
		ur.user_id = user.id
		sess.add(ur)

		sess.commit()

		return jsonify(dict(status='user created', _id=_id))

'''
Authenticate with username or password
'''
@ent.route("/login", methods=['POST'])
@cross_origin()
def login():
	#clean login credentials - strip whitespace and convert to lowercase
	username = req.form.get('username', '').strip().lower()
	email = req.form.get('email', '').strip().lower()
	
	#check if user exists in DB
	try:
		user = dbo.sess.query(User).filter(and_(or_(User.username==username, User.email==email), User.email !=None)).one()
		password = req.form.get('password', '')

		#check if password matches
		if checkpw(password.encode(), user.password):

			#get roles
			with dbo.engine.connect() as con:
				roles = con.execute(text(f'''
					SELECT 
						r.role 
						,r.id 
					FROM roles AS r 
					LEFT JOIN users_roles AS ur ON r.id=ur.role_id 
					LEFT JOIN users AS u ON ur.user_id=u.id 
					WHERE u.id='{user.id}' 
				''')).fetchall()
				roles = [role.role for role in roles]

			#get permissions
			with dbo.engine.connect() as con:
				permissions = con.execute(text(f'''
					SELECT m.module, mr.permissions 
					FROM users AS u 
						LEFT JOIN users_roles AS ur ON u.id=ur.user_id 
						LEFT JOIN roles AS r ON ur.role_id=r.id 
						LEFT JOIN modules_roles AS mr ON r.id=mr.role_id 
						LEFT JOIN modules AS m ON mr.module_id=m.id 
					WHERE u.id='{user.id}' AND m.module IS NOT NULL
					GROUP BY m.module, mr.permissions 
					UNION 
					SELECT m.module, mu.permissions 
					FROM users AS u 
						LEFT JOIN modules_users AS mu ON u.id=mu.user_id 
						LEFT JOIN modules AS m ON mu.module_id=m.id
					WHERE u.id='{user.id}' AND m.module IS NOT NULL
					GROUP BY m.module, mu.permissions 
				''')
				).fetchall()
				permissions = [dict(module=p.module, permissions=p.permissions) for p in permissions]

			#get previous login before setting current login to now
			last_login = user.last_login if user.last_login != user.created_at else datetime(1, 1, 1, 1, 1, 1)
			user.last_login = datetime.now()
			user.status = True #set login status to 1
			user.token = tokenize(user) #create a JWT token to allow login from multiple machines

			dbo.sess.commit()

			return jsonify(
				dict(
					_id=user._id, 
					email=user.email, 
					username=user.username, 
					since=user.created_at, 
					last_login = last_login, 
					roles = roles, 
					permissions = permissions,
					token = user.token, 
					status = 'authenticated'
				)
			)
		else:
			return jsonify(dict(msg='authentication failed', status='error'))	
	except:
		return jsonify(dict(msg='user does not exist', status='error'))

'''
Logout of account
'''
@ent.route("/logout/<_id>", methods=['POST', 'GET'])
def logout(_id):
	try:
		#intantiate use object
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		user.status = False #set login status to flase
		user.token = reset_token(user) #reset token so all other accounts are logged out
		dbo.sess.commit()
		return jsonify(dict(status='logged out', _id=_id))
	except:
		return jsonify(dict(status='error', msg='user does not exist or some other bad thing happend'))


'''
Admin Methods
------------------------------------------------------------------------------------------
'''

'''
Get all users
'''
@ent.route('/get_users', methods=['POST', 'GET'])
@cross_origin()
def get_users():
	users = [ dict(
		_id=user._id, 
		username=user.username, 
		email=user.email, 
		since=user.created_at, 
		last_login=user.last_login, 
		loggedin='yes' if user.status == True else 'no',
		verified='yes' if user.verified == True else 'no'

		) for user in dbo.sess.query(User).all()]
	return jsonify(dict(users=users))


'''
Get details for a particular user
'''
@ent.route('/get_user/<_id>',methods=['POST'])
@cross_origin()
def get_user(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()

		#get roles
		with dbo.engine.connect() as con:
			roles = con.execute(text(f'''
				SELECT 
					r.role 
					,r.id 
				FROM roles AS r 
				LEFT JOIN users_roles AS ur ON r.id=ur.role_id 
				LEFT JOIN users AS u ON ur.user_id=u.id 
				WHERE u.id='{user.id}' 
			''')).fetchall()
			roles = [role.role for role in roles]

		#get permissions
		with dbo.engine.connect() as con:
			permissions = con.execute(text(f'''
				SELECT m.module, mr.permissions 
				FROM users AS u 
					LEFT JOIN users_roles AS ur ON u.id=ur.user_id 
					LEFT JOIN roles AS r ON ur.role_id=r.id 
					LEFT JOIN modules_roles AS mr ON r.id=mr.role_id 
					LEFT JOIN modules AS m ON mr.module_id=m.id 
				WHERE u.id='{user.id}' AND m.module IS NOT NULL
				GROUP BY m.module, mr.permissions 
				UNION 
				SELECT m.module, mu.permissions 
				FROM users AS u 
					LEFT JOIN modules_users AS mu ON u.id=mu.user_id 
					LEFT JOIN modules AS m ON mu.module_id=m.id
				WHERE u.id='{user.id}' AND m.module IS NOT NULL
				GROUP BY m.module, mu.permissions 
			''')
			).fetchall()
			permissions = [dict(module=p.module, permissions=p.permissions) for p in permissions]

		return jsonify(dict(
			status='success', 
			_id=user._id,
			username=user.username, 
			email=user.email, 
			since=user.created_at,
			roles = roles,
			permissions = permissions, 
			last_login=user.last_login, 
			loggedin='yes' if user.status == True else 'no',
			verified='yes' if user.verified == True else 'no'
		))
	except:
		return jsonify(dict(status='error', msg='the user was not found'))

'''
DELETE a particular user
'''
@ent.route('/delete_user/<_id>', methods=['DELETE'])
@cross_origin()
def delete_user(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		if user.id == 1: #check to exculde super user
			return jsonify(dict(status='error', msg='you are not allowed to delete the superuser account'))

		dbo.sess.delete(user)
		dbo.sess.commit()
		return jsonify(dict(status='success', msg='the user was deleted'))
	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='the user was not found'))

	return jsonify(dict(status='error', msg='unknown'))

'''
DELETE all users
'''
@ent.route('/flush_users', methods=['DELETE'])
@cross_origin()
def flush_users():
	with dbo.engine.connect() as con:
		con.execute(text("DELETE FROM users WHERE id > 1")) #delete all except super user
		return jsonify(dict(status='success', msg='all users have been successfully deleted'))

'''
Update a users password
'''
@ent.route("/reset_password/<_id>", methods=['PUT'])
@cross_origin()
def reset_password(_id):
	keys = [item for item in req.form]

	#expects password to be included in request
	if 'password' not in keys:
		return jsonify(dict(status='error', msg='no password'))

	password = req.form.get('password', None).strip()

	#username must be at least 8 characters in length and 
	if len(password) < 8:
		return jsonify(dict(status='error', message='password is less than 8 characters long'))

	#password must contain lowecase, uppercase, number and special character and 
	if re.search(r'[a-z]+', password) == None or re.search(r'[A-Z]+', password) == None or re.search(r'[0-9]+', password) == None or re.search(r'[_.$@*!+#%&-]+', password) == None: 
		return jsonify(dict(status='error', message='password must contain lowercase, uppercase, number and special character'))

	#instantiate user
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	_id = user._id
	user.password = hashpw(password.encode(), gensalt()) #encrypt and reset password
	dbo.sess.commit()

	return jsonify(dict(status='success', msg=f'password for {_id} successfully updated'))


'''
Verify a user account example by phone or email
'''
@ent.route("/verify/<_id>")
@cross_origin()
def verify(_id):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	user.verified = True
	_id = user._id
	dbo.sess.commit()
	return jsonify(dict(status='success', msg=f'user {_id} was successfully verified'))

'''
Helper methods are below this comment
------------------------------------------------------------------------------------------
'''

'''
Create JWT Token
'''
def tokenize(user):
	#check if token is expired
	try:
		#if token is not expired return the same token
		if jwt.decode(user.token, user.secret, algorithms=["HS256"])['exp'] > datetime.now():
			return user.token
	except:
		#if token is expired generate a new one
		payload = dict(
			iat = datetime.now(), 
			exp = datetime.now() + timedelta(days=7), 
			username = user.username,
			email = user.email,
			_id = user._id
		)
		return jwt.encode(payload, user.secret, algorithm="HS256")

'''
Create JWT Token as replacement
'''
def reset_token(user):
	#forcefully create a new token
	payload = dict(
		iat = datetime.now(), 
		exp = datetime.now() + timedelta(days=7), 
		username = user.username,
		email = user.email,
		_id = user._id
	)
	return jwt.encode(payload, user.secret, algorithm="HS256")


'''
Create expired JWT Token
'''
def init_token(user):
	#create an expired token - useful for signup with no prior login
	payload = dict(
		iat = datetime.now(), 
		exp = datetime.now() - timedelta(days=7), 
		username = user.username,
		email = user.email,
		_id = user._id
	)
	return jwt.encode(payload, user.secret, algorithm="HS256")