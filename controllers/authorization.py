from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
import re
from models.dbo import *



ori = Blueprint('ori', __name__, url_prefix='/ori')
sqlite_path = ori.root_path.replace('controllers', 'dbs/autheo.db')
dbo = DBO(sqlite_path)

'''
Create a new role
'''
@ori.route("/create_role", methods=['POST'])
@cross_origin()
def create_role():
	role=req.form.get('role', 'none')
	description=req.form.get('description', '')

	if role == 'none':
		return jsonify(dict(status='error', msg='there is no row name'))

	if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', role) == None:
		return jsonify(dict(status='error', msg='the role includes illegal characters'))	

	if re.search(r'([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]+)', description) == None:
		return jsonify(dict(status='error', msg='the description includes illegal characters'))	

	role = role.strip().replace(' ', '_').lower()
	description = description.strip()

	if len(dbo.sess.query(Role).filter_by(role=role).all()) > 0:
		return jsonify(dict(status='error', msg='the role already exists'))

	new_role = Role()
	new_role.role = role
	new_role.description = description

	dbo.sess.add(new_role)
	dbo.sess.commit()		

	return jsonify(dict(status='role created', role_id=dbo.sess.query(Role).filter_by(role=role).one().id))

'''
Get all roles
'''
@ori.route("/get_roles", methods=['POST'])
@cross_origin()
def get_roles():
	roles = [dict(id=role.id, role=role.role, description=role.description) for role in dbo.sess.query(Role).all()]	
	return jsonify(dict(status='success', roles=roles))


'''
Get all roles for a user
'''
@ori.route("/get_roles/<user_id>", methods=['POST'])
@cross_origin()
def get_user_roles(user_id):
	roles = dbo.engine.execute('''
		SELECT r.id, r.role 
		FROM roles AS r 
		LEFT JOIN users_roles AS ur ON r.id=ur.role_id 
		LEFT JOIN users AS u ON ur.user_id=u.id 
		WHERE u._id='{_id}'
	'''.format(_id=user_id)).fetchall()
	roles = [dict(id=role.id, role=role.role) for role in roles]	
	return jsonify(dict(status='success', roles=roles))


'''
Update an existing user defined role
'''
@ori.route("/update_role/<orole>", methods=['POST'])
@cross_origin()
def update_role(orole):
	role=req.args.get('role', 'none')
	description=req.args.get('description', '')

	if role == 'none':
		return jsonify(dict(status='error', msg='there is no row name'))

	if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', role) == None:
		return jsonify(dict(status='error', msg='the role includes illegal characters'))	

	if re.search(r'([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]+)', description) == None:
		return jsonify(dict(status='error', msg='the description includes illegal characters'))	

	role = role.strip().replace(' ', '_').lower()
	description = description.strip()

	if len(dbo.sess.query(Role).filter_by(role=orole).all()) != 1:
		return jsonify(dict(status='error', msg='the role you want to update does not exists'))

	draft_role = dbo.sess.query(Role).filter_by(role=orole).one()

	if draft_role.id in (1, 2, 3):
		return jsonify(dict(status='error', msg='you cannot edit/update the base roles'))

	draft_role.role = role
	draft_role.description = description

	try:
		dbo.sess.commit()
		return jsonify(dict(status='role updated', role_id=dbo.sess.query(Role).filter_by(role=role).one().id))
	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='the role name you are updating to already exists'))

'''
Delete existing user defined role
'''
@ori.route("/delete_role/<role>", methods=['POST'])
@cross_origin()
def delete_role(role):
	if len(dbo.sess.query(Role).filter_by(role=role).all()) != 1:
		return jsonify(dict(status='error', msg='the role you want to delete does not exists'))

	role = dbo.sess.query(Role).filter_by(role=role).one()
	_id = role.id

	if _id in (1, 2, 3):
		return jsonify(dict(status='error', msg='you cannot delete the base roles'))

	dbo.sess.delete(role)
	return jsonify(dict(status='deleted', id=_id))

'''
Assign Role to a User
'''
@ori.route("/asign_role/<_id>/<role_id>", methods=['POST'])
@cross_origin()
def assign_role(_id, role_id):
	return jsonify(dict(status='success'))

'''
Remove Role from a User
'''
@ori.route("/remove_role/<role_id>", methods=['POST'])
@cross_origin()
def remove_role(role_id):
	return jsonify(dict(status='success'))

'''
Remove all User Roles
'''
@ori.route("/remove_all_user_roles/<_id>", methods=['POST'])
@cross_origin()
def remove_all_user_roles(_id):
	return jsonify(dict(status='success'))


'''
MODULES
-----------------------------------------------------------------------
'''

'''
Register a module
'''
@ori.route("/register_module/<module>", methods=['POST'])
@cross_origin()
def register_module(module):
	return jsonify(dict(status='success'))

@ori.route("/register_modules", methods=['POST'])
@cross_origin()
def register_modules():
	return jsonify(dict(status='success'))

@ori.route("/remove_module/<module_id>", methods=['POST'])
@cross_origin()
def remove_module(module_id):
	return jsonify(dict(status='success'))

@ori.route("/flush_modules", methods=['POST'])
@cross_origin()
def flush_modules():
	return jsonify(dict(status='success'))

@ori.route("/add_role_privilege/<module_id>/<role_id>/<permission>", methods=['POST'])
@cross_origin()
def add_role_privilege(module_id, role_id, permission):
	return jsonify(dict(status='success'))

@ori.route("/add_user_privilege/<module_id>/<_id>/<permission>", methods=['POST'])
@cross_origin()
def add_user_privilege(module_id, _id, permission):
	return jsonify(dict(status='success'))

@ori.route("/flush_role_privileges/<module_id>/<role_id>", methods=['POST'])
@cross_origin()
def flush_role_privileges(module_id, role_id):
	return jsonify(dict(status='success'))

@ori.route("/flush_user_privileges/<module_id>/<_id>", methods=['POST'])
@cross_origin()
def flush_user_privileges(module_id, _id):
	return jsonify(dict(status='success'))
