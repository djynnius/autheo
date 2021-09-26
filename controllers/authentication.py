from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
from sqlalchemy import or_, and_, not_
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
	username = req.form.get('username', 'none').strip()
	email = req.form.get('email', 'none').strip()
	password = req.form.get('password', 'none').strip()

	#username validator
	if username != 'none':
		#username must be at least 8 characters in length and 
		if len(username) < 8:
			return jsonify(dict(status='error', message='username is less than 8 characters long'))
		#can contain only lettres, number, underscores and dots
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9_]+)$', username) == None:
			return jsonify(dict(status='error', message='username can only contain numbers and letters, underscore and dot. username cannot start with a number, underscore or dor nor can it end with a dot or underscore'))

	#email validator
	if email != 'none':
		#username must be at least 8 characters in length and 
		if re.search(r'^([a-zA-Z]+)([a-zA-Z0-9_.]+)([a-zA-Z0-9]+)@([a-zA-Z]+).([a-zA-Z.]{2,5})$', email) == None:
			return jsonify(dict(status='error', message='this is not a valid email'))

	if password != 'none':
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
	people = dbo.engine.execute("SELECT id FROM users WHERE username='{user}' OR email='{email}'".format(user=username, email=email)).fetchall()
	if len(people) > 0:
		return jsonify(dict(status='error', message='a user with these credentials already exists'))

	user = User()
	user.username = username
	user.email = email
	user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()) #encrypt password
	user.secret = bcrypt.hashpw(str(datetime.now()).encode(), bcrypt.gensalt())[2:32] #make user unique secret for JWT
	user.token = init_token(user) #set initial JWT token which is already expired
	dbo.sess.add(user)
	dbo.sess.commit()

	#set a unique identifier hash
	person = dbo.engine.execute(
		'''	SELECT * 
			FROM users 
			WHERE username='{user}' OR email='{email}'
		'''.format(user=username, email=email)
	).fetchone()

	user = dbo.sess.query(User).filter_by(id=person.id).one()
	#create hash version of id
	_id = hashlib.md5("{uid}_{uat}".format(uid=person.id, uat=person.created_at).encode()).hexdigest()
	user._id = _id
	dbo.sess.commit()

	return jsonify(dict(status='user created', _id=_id))

'''
Authenticate with username or password
'''
@ent.route("/login", methods=['POST'])
@cross_origin()
def login():
	#clean login credentials - strip whitespace and convert to lowercase
	username = req.form.get('username', 'none').lower().strip()
	email = req.form.get('email', 'none').lower().strip()
	
	#check if user exists in DB
	try:
		user = dbo.sess.query(User).filter(and_(or_(User.username==username, User.email==email), User.email !='none')).one()
		password = req.form.get('password', 'none').strip()

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

			#get previous login before setting current login to now
			last_login = user.last_login if user.last_login != user.created_at else datetime(1, 1, 1, 1, 1, 1)
			user.last_login = datetime.now()
			user.status = 1 #set login status to 1
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
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		user.status = 0
		user.token = reset_token(user)
		dbo.sess.commit()
		return jsonify(dict(status='logged out', _id=_id))
	except:
		return jsonify(dict(status='error', msg='user does not exist or some other bad thing happend'))


'''
Admin Methods
------------------------------------------------------------------------------------------
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
		loggedin='yes' if user.status == True else 'no'
		) for user in dbo.sess.query(User).all()]
	return jsonify(dict(users=users))


@ent.route('/get_user/<_id>',methods=['POST'])
@cross_origin()
def get_user(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		return jsonify(dict(
			status='success', 
			_id=user._id,
			username=user.username, 
			email=user.email, 
			since=user.created_at, 
			last_login=user.last_login, 
			loggedin='yes' if user.status == True else 'no'
		))
	except:
		return jsonify(dict(status='error', msg='the user was not found'))


@ent.route('/delete_user/<_id>', methods=['DELETE'])
@cross_origin()
def delete_user(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		if user.id == 1:
			return jsonify(dict(status='error', msg='you are not allowed to delete the superuser account'))

		dbo.sess.delete(user)
		dbo.sess.commit()
		return jsonify(dict(status='success', msg='the user was deleted'))
	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='the user was not found'))

	return jsonify(dict(status='error', msg='unknown'))

@ent.route('/flush_users', methods=['DELETE'])
@cross_origin()
def flush_users():
	dbo.engine.execute("DELETE FROM users WHERE id > 1")
	return jsonify(dict())



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