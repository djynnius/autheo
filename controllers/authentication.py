from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
from sqlalchemy import or_, and_, not_
from sqlalchemy.orm import Session
import re
import jwt
import bcrypt
import hashlib
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
	username = req.form.get('username', None)
	email = req.form.get('email', None)
	password = req.form.get('password', None)

	#username validator
	if username != None:
		#username must be at least 8 characters in length and 
		if len(username) < 8:
			return jsonify(dict(status='error', message='username is less than 8 characters long'))
		#can contain only lettres, number, underscores and dots
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9_]+)$', username) == None:
			return jsonify(dict(status='error', message='username can only contain numbers and letters, underscore and dot. username cannot start with a number, underscore or dor nor can it end with a dot or underscore'))

	#email validator
	if email != None:
		#username must be at least 8 characters in length and 
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9]+)@([a-zA-Z]+).([a-zA-Z.]{2,5})$', email) == None:
			return jsonify(dict(status='error', message='this is not a valid email'))

	if password != None:
		#username must be at least 8 characters in length and 
		if len(password) < 8:
			return jsonify(dict(status='error', message='password is less than 8 characters long'))
		#password must contain lowecase, uppercase, number and special character and 
		if re.search(r'[a-z]+', password) == None or re.search(r'[A-Z]+', password) == None or re.search(r'[0-9]+', password) == None or re.search(r'[_.$@*!+#%&-]+', password) == None: 
			return jsonify(dict(status='error', message='password must contain lowercase, uppercase, number and special character'))

	#convert username and email to all lowercase since not case sensitive
	username = username
	email = email

	#check if the user exists
	people = dbo.engine.execute("SELECT id FROM users WHERE (username='{user}' AND username IS NOT NULL) OR (email='{email}' AND email IS NOT NULL)".format(user=username, email=email)).fetchall()
	if len(people) > 0:
		return jsonify(dict(status='error', message='a user with these credentials already exists'))

	#instantiate user object
	user = User()
	user.username = username
	user.email = email
	user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) #encrypt password
	user.secret = bcrypt.hashpw(str(datetime.now()).encode(), bcrypt.gensalt())[2:32] #make user unique secret for JWT
	user.token = init_token(user) #set initial JWT token which is already expired
	dbo.sess.add(user)
	dbo.sess.commit()

	with Session(dbo.engine) as sess:
		#set a unique identifier hash
		person = dbo.engine.execute(
			'''	SELECT * 
				FROM users 
				WHERE username='{user}' OR email='{email}'
			'''.format(user=username, email=email)
		).fetchone()

		user = sess.query(User).filter_by(id=person.id).one()
		#create hash version of id
		_id = hashlib.md5("{uid}_{uat}".format(uid=person.id, uat=person.created_at).encode()).hexdigest()
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
	username = req.form.get('username', None)
	email = req.form.get('email', None)
	
	#check if user exists in DB
	try:
		user = dbo.sess.query(User).filter(and_(or_(User.username==username, User.email==email), User.email !=None)).one()
		password = req.form.get('password', None)

		#check if password matches
		if bcrypt.checkpw(password.encode(), user.password):

			#get roles
			roles = dbo.engine.execute('''
				SELECT 
					r.role 
					,r.id 
				FROM roles AS r 
				LEFT JOIN users_roles AS ur ON r.id=ur.role_id 
				LEFT JOIN users AS u ON ur.user_id=u.id 
				WHERE u.id='{user_id}' 
			'''.format(user_id=user.id)).fetchall()
			roles = [role.role for role in roles]

			#get permissions
			permissions = dbo.engine.execute('''
				SELECT m.module, mr.permissions 
				FROM users AS u 
					LEFT JOIN users_roles AS ur ON u.id=ur.user_id 
					LEFT JOIN roles AS r ON ur.role_id=r.id 
					LEFT JOIN modules_roles AS mr ON r.id=mr.role_id 
					LEFT JOIN modules AS m ON mr.module_id=m.id 
				WHERE u.id='{uid}' AND m.module IS NOT NULL
				GROUP BY m.module, mr.permissions 
				UNION 
				SELECT m.module, mu.permissions 
				FROM users AS u 
					LEFT JOIN modules_users AS mu ON u.id=mu.user_id 
					LEFT JOIN modules AS m ON mu.module_id=m.id
				WHERE u.id='{uid}' AND m.module IS NOT NULL
				GROUP BY m.module, mu.permissions 
			'''.format(uid=user.id)
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
@ent.route('/get_users', methods=['POST'])
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
		roles = dbo.engine.execute('''
			SELECT 
				r.role 
				,r.id 
			FROM roles AS r 
			LEFT JOIN users_roles AS ur ON r.id=ur.role_id 
			LEFT JOIN users AS u ON ur.user_id=u.id 
			WHERE u.id='{user_id}' 
		'''.format(user_id=user.id)).fetchall()
		roles = [role.role for role in roles]

		#get permissions
		permissions = dbo.engine.execute('''
			SELECT m.module, mr.permissions 
			FROM users AS u 
				LEFT JOIN users_roles AS ur ON u.id=ur.user_id 
				LEFT JOIN roles AS r ON ur.role_id=r.id 
				LEFT JOIN modules_roles AS mr ON r.id=mr.role_id 
				LEFT JOIN modules AS m ON mr.module_id=m.id 
			WHERE u.id='{uid}' AND m.module IS NOT NULL
			GROUP BY m.module, mr.permissions 
			UNION 
			SELECT m.module, mu.permissions 
			FROM users AS u 
				LEFT JOIN modules_users AS mu ON u.id=mu.user_id 
				LEFT JOIN modules AS m ON mu.module_id=m.id
			WHERE u.id='{uid}' AND m.module IS NOT NULL
			GROUP BY m.module, mu.permissions 
		'''.format(uid=user.id)
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
	dbo.engine.execute("DELETE FROM users WHERE id > 1") #delete all except super user
	return jsonify(dict(status='success', msg='all users have been successfully deleted'))

'''
Update a users password
'''
@ent.route("/update_password/_id", methods=['PUT'])
@cross_origin()
def update_password(_id):
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
	user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) #encrypt and reset password
	dbo.sess.commit()

	return jsonify(dict(status='success', msg='password for {_id} successfully updated'.format(_id=_id)))


'''
Verify a user account example by phone or email
'''
@ent.route("/verify/<_id>")
@cross_origin()
def verify(_id):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	user.verify = True
	_id = user._id
	dbo.sess.commit()
	return jsonify(dict(status='success', msg='user {_id} was successfully verified'.format(_id=_id)))

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