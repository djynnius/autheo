from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
import re
import bcrypt
import hashlib
from datetime import datetime
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

	username = req.form.get('username', 'none')
	email = req.form.get('email', 'none')
	password = req.form.get('password', 'none')

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

	people = dbo.engine.execute("SELECT id FROM users WHERE username='{user}' OR email='{email}'".format(user=username, email=email)).fetchall()
	if len(people) > 0:
		return jsonify(dict(status='error', message='a user with these credentials already exists'))

	user = User()
	user.username = username
	user.email = email
	user.password = password
	dbo.sess.add(user)
	dbo.sess.commit()

	person = dbo.engine.execute(
		'''	SELECT * 
			FROM users 
			WHERE username='{user}' OR email='{email}'
		'''.format(user=username, email=email)
	).fetchone()

	user = dbo.sess.query(User).filter_by(id=person.id).one()
	user._id = hashlib.md5("{uid}_{uat}".format(uid=person.id, uat=person.created_at).encode()).hexdigest()
	dbo.sess.commit()



	return jsonify(dict(status='success', data=req.form))

@ent.route("/login", methods=['POST'])
def login():
	return jsonify(dict(status='success'))