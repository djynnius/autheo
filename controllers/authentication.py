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


@ent.route("/signup", methods=['POST'])
@cross_origin()
def signup():
	#be at least 8 characters
	keys = [item for item in req.form]
	if 'password' not in keys:
		return jsonify(dict(status='error', msg='no password'))

	#expects one or more of username or email
	if 'email' not in keys and 'username' not in keys:
		return jsonify(dict(status='error', message='no username or email'))

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

	password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
	username = username.lower()
	email = email.lower()

	#check if the user exists
	people = dbo.engine.execute("SELECT id FROM users WHERE username='{user}' OR email='{email}'".format(user=username, email=email)).fetchall()
	if len(people) > 0:
		return jsonify(dict(status='error', message='a user with these credentials already exists'))

	user = User()
	user.username = username
	user.email = email
	user.password = password
	user.secret = bcrypt.hashpw(str(datetime.now()).encode(), bcrypt.gensalt())[2:32]
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
	_id = hashlib.md5("{uid}_{uat}".format(uid=person.id, uat=person.created_at).encode()).hexdigest();
	user._id = _id
	dbo.sess.commit()

	return jsonify(dict(status='success', _id=_id))


@ent.route("/login", methods=['POST'])
@cross_origin()
def login():
	
	username = req.form.get('username', 'none').lower().strip()
	email = req.form.get('email', 'none').lower().strip()
	
	try:
		user = dbo.sess.query(User).filter(or_(User.username==username, User.email==email)).one()
		password = req.form.get('password', 'none').strip()
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


			last_login = user.last_login if user.last_login != user.created_at else datetime(1, 1, 1, 1, 1, 1)
			user.last_login = datetime.now()
			user.status = 1 
			user.token = tokenize(user)

			dbo.sess.commit()

			return jsonify(dict(
				status='success', 
				user=dict(
					_id=user._id, 
					email=user.email, 
					username=user.username, 
					since=user.created_at, 
					last_login = last_login, 
					roles = roles, 
					token = user.token
				)
			))
		else:
			return jsonify(dict(msg='authentication failed', status='error'))	
	except:
		return jsonify(dict(msg='user does not exist', status='error'))
	
@ent.route("/logout/<_id>", methods=['POST', 'GET'])
def logout(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		user.status = 0
		user.token = reset_token(user)
		dbo.sess.commit()
		return jsonify(dict(status='success', _id=_id))
	except:
		return jsonify(dict(status='error', msg='user does not exist or some other bad thing happend'))

'''
Helper methods are below this comment
'''
def tokenize(user):
	try:
		if jwt.decode(user.token, user.secret, algorithms=["HS256"])['exp'] > datetime.now():
			return user.token
	except:
		payload = dict(
			iat = datetime.now(), 
			exp = datetime.now() + timedelta(days=7), 
			username = user.username,
			email = user.email,
			_id = user._id
		)
		return jwt.encode(payload, user.secret, algorithm="HS256")

def reset_token(user):
	payload = dict(
		iat = datetime.now(), 
		exp = datetime.now() + timedelta(days=7), 
		username = user.username,
		email = user.email,
		_id = user._id
	)
	return jwt.encode(payload, user.secret, algorithm="HS256")
