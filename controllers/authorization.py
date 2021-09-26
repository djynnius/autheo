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
@ori.route("/assign_role/<_id>/<orole>", methods=['POST'])
@cross_origin()
def assign_role(_id, orole):

	assignments = dbo.engine.execute('''
		SELECT ur.id 
		FROM users_roles AS ur 
		LEFT JOIN users AS u ON ur.user_id=u.id 
		LEFT JOIN roles AS r ON ur.role_id=r.id
		WHERE u._id='{_id}' AND r.role='{orole}'
	'''.format(_id=_id, orole=orole)).fetchall()

	if len(assignments) > 0:
		return jsonify(dict(status='error', msg='this role has already been assigned'))

	user = dbo.sess.query(User).filter_by(_id=_id).one()
	role = dbo.sess.query(Role).filter_by(role=orole).one()

	ur = UserRole()
	ur.user_id=user.id
	ur.role_id=role.id
	dbo.sess.add(ur)
	dbo.sess.commit()
	return jsonify(dict(status='role of {role} successfully assgned to {_id}'.format(role=orole, _id=_id)))

'''
Remove Role from a User
'''
@ori.route("/remove_role_from_user/<_id>/<role>", methods=['POST'])
@cross_origin()
def remove_role(_id, role):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	role = dbo.sess.query(Role).filter_by(role=role).one()
	dbo.engine.execute('''
		DELETE FROM users_roles 
		WHERE user_id = '{uid}' AND role_id='{rid}' AND id > 1
	'''.format(uid=user.id, rid=role.id))
	return jsonify(dict(status='deleted'))

'''
Remove all Roles for a particular User
'''
@ori.route("/remove_all_roles_from_user/<_id>", methods=['POST'])
@cross_origin()
def remove_all_user_roles(_id):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	dbo.engine.execute('''
		DELETE FROM users_roles 
		WHERE user_id = '{uid}' AND id > 1
	'''.format(uid=user.id))
	return jsonify(dict(status='deleted'))

'''
Flush all User Roles
'''
@ori.route("/flush_user_roles", methods=['POST'])
@cross_origin()
def flush_user_roles():
	dbo.engine.execute('''
		DELETE FROM users_roles 
		WHERE id > 1
	''')
	return jsonify(dict(status='user roles flushed'))	


'''
MODULES
-----------------------------------------------------------------------
'''

'''
Register a module
'''
@ori.route("/register_module/<name>/<description>", methods=['POST'])
@cross_origin()
def register_module(name, description=''):

	if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', name) == None:
		return jsonify(dict(status='error', msg='the module includes illegal characters'))	

	if re.search(r'([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]+)', description) == None:
		return jsonify(dict(status='error', msg='the description includes illegal characters'))	

	module = Module()
	module.module = name.strip().replace(' ', '_')
	module.description = description.strip()
	
	try:
		dbo.sess.add(module)
		dbo.sess.commit()
		return jsonify(dict(status='module successfully added'))
	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='the module already exists'))

'''
Register multiple modules using aruments in url string 
http://autheo.io/register_modules?1=News&2=Articles&3=Blog
Does not include description
'''
@ori.route("/register_modules", methods=['POST'])
@cross_origin()
def register_modules():
	modules = [a.strip().replace(' ', '_') for i,a in req.args.items()]
	status = 'success'
	successful = []
	failed = []

	for module in modules:
		if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', module) == None:
			return jsonify(dict(status='error', msg='one or more modules includes illegal characters'))		

		item = Module()
		item.module = module

		try:
			dbo.sess.add(item)
			dbo.sess.commit()
			successful.append(module)
		except:
			dbo.sess.rollback()
			failed.append(module)
			status = 'error'

	return jsonify(dict(status='completed', success=successful, failed=failed))

'''
Remove a module
'''
@ori.route("/remove_module/<module>", methods=['POST'])
@cross_origin()
def remove_module(module):
	try:
		imodule = dbo.sess.query(Module).filter_by(module=module).one()
		dbo.sess.delete(imodule)
		dbo.sess.commit()
	except:
		dbo.sess.rollback()

	return jsonify(dict(status='{} successfully removed'.format(module.capitalize())))

'''
Removes all modules at once!
'''
@ori.route("/flush_modules", methods=['POST'])
@cross_origin()
def flush_modules():
	dbo.engine.execute('''
		DELETE FROM modules
	''')
	return jsonify(dict(status='All modules successfully removed'))

'''
View all modules
'''
@ori.route("/get_modules", methods=['POST'])
@cross_origin()
def get_modules():
	modules = [dict(module=module.module, id=module.id, description=module.description) for module in dbo.sess.query(Module).all()]
	return jsonify(dict(status='success', modules=modules))

'''
Add priviledges to a module for a role so everyone with that role inherits those permissions
The Unix standard is used
0 = no permission, 
1 = Basic eg read only
2 = Edit/Write priviledged without read priviledges
3 = Read and Write access
4 = Highest single priviledge eg Execute, Delete
5 = Read and Execute/Delete
6 = Write and Execute/Delete but not Read
7 = Full priviledges ie Read Edit/Write and Execute/Delete
'''
@ori.route("/set_role_permissions/<module>/<role>/<permission>", methods=['POST'])
@cross_origin()
def set_role_permissions(module, role, permission):
	module = module.strip().lower()
	role = role.strip().lower()
	permission = int(permission)
	
	mrs = dbo.engine.execute('''
		SELECT mr.id, mr.module_id, mr.role_id
		FROM modules_roles AS mr 
			LEFT JOIN modules AS m ON mr.module_id=m.id 
			LEFT JOIN roles AS r ON mr.role_id=r.id
		WHERE LOWER(m.module)='{module}' AND LOWER(r.role)='{role}'
	'''.format(module=module, role=role)).fetchall()

	try:
		omodule = dbo.engine.execute("SELECT * FROM modules WHERE LOWER(module)='{module}'".format(module=module)).fetchone()
		orole = dbo.sess.query(Role).filter_by(role=role).one()
		if len(mrs) == 0:
			mr = ModuleRole()
			mr.module_id = omodule.id
			mr.role_id = orole.id
			mr.permissions = permission
			dbo.sess.add(mr)
		elif len(mrs) == 1:
			mr = ModuleRole(id=mrs[0].id)
			mr.module_id = omodule.id
			mr.role_id = orole.id
			mr.permissions = permission			
		else:
			return jsonify(dict(status='error', msg='unknown: possibly multiple instances of module role'))

		dbo.sess.commit()
		return jsonify(dict(status='success', msg='permissions updated'))

	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='unknown: possibly module or role does not exist'))

	return jsonify(dict(status='error', msg='unknown'))

'''
Set permissions that are specific to users
'''
@ori.route("/set_user_permissions/<module>/<_id>/<permission>", methods=['POST'])
@cross_origin()
def set_user_permissions(module_id, _id, permission):
	module = module.strip().lower()
	permission = int(permission)
	
	mus = dbo.engine.execute('''
		SELECT mu.id, mu.module_id, mu.user_id
		FROM modules_users AS mu 
			LEFT JOIN modules AS m ON mu.module_id=m.id 
			LEFT JOIN users AS u ON mu.user_id=u.id
		WHERE LOWER(m.module)='{module}' AND u._id='{_id}'
	'''.format(module=module, _id=_id)).fetchall()

	try:
		omodule = dbo.engine.execute("SELECT * FROM modules WHERE LOWER(module)='{module}'".format(module=module)).fetchone()
		ouser = dbo.sess.query(User).filter_by(_id=_id).one()
		if len(mus) == 0:
			mu = ModuleUser()
			mu.module_id = omodule.id
			mu.user_id = ouser.id
			mu.permissions = permission
			dbo.sess.add(mu)
		elif len(mus) == 1:
			mu = ModuleUser(id=mrs[0].id)
			mu.module_id = omodule.id
			mu.user_id = ouser.id
			mu.permissions = permission			
		else:
			return jsonify(dict(status='error', msg='unknown: possibly multiple instances of module user'))

		dbo.sess.commit()
		return jsonify(dict(status='success', msg='permissions updated'))

	except:
		dbo.sess.rollback()
		return jsonify(dict(status='error', msg='unknown: possibly module or role does not exist'))

	return jsonify(dict(status='error', msg='unknown'))

'''
Remove all role permissions for a particular module
'''
@ori.route("/remove_role_permissions/<module>", methods=['POST'])
@cross_origin()
def remove_role_permissions(module):
	module = dbo.engine.execute("SELECT * FROM modules WHERE LOWER(module)='{module}'".format(module=module)).fetchone()
	dbo.engine.execute('''
		DELETE FROM modules_roles WHERE module_id='{mid}'
	'''.format(mid=module.id))	
	return jsonify(dict(status='success'))

'''
Remove all permissions in the modules_roles table
'''
@ori.route("/flush_role_permissions", methods=['POST'])
@cross_origin()
def flush_role_permissions():
	dbo.engine.execute('''
		DELETE FROM modules_roles
	''')	
	return jsonify(dict(status='success'))

'''
Remove user permissions for a particular module
'''
@ori.route("/remove_user_permissions/<module>", methods=['POST'])
@cross_origin()
def remove_user_permissions(module):
	module = dbo.engine.execute("SELECT * FROM modules WHERE LOWER(module)='{module}'".format(module=module)).fetchone()
	dbo.engine.execute('''
		DELETE FROM modules_users WHERE module_id='{mid}'
	'''.format(mid=module.id))	
	return jsonify(dict(status='success'))

'''
Remove all permissions in the modules_users table
'''
@ori.route("/flush_user_permissions", methods=['POST'])
@cross_origin()
def flush_user_permissions():
	dbo.engine.execute('''
		DELETE FROM modules_users
	''')	
	return jsonify(dict(status='success'))
