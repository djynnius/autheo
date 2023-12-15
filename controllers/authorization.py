from flask import Blueprint, jsonify, request as req
from flask_cors import cross_origin
import re
from models.dbo import *
from sqlalchemy import text


ori = Blueprint('ori', __name__, url_prefix='/ori')
sqlite_path = ori.root_path.replace('controllers', 'dbs/autheo.db')
dbo = DBO(sqlite_path)

'''
Create a new role
'''
@ori.route("/create_role/<role>/<description>", methods=['POST'])
@cross_origin()
def create_role(role, description):

	if role == None:
		return jsonify(dict(status='error', msg='there is no role name'))

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
@ori.route("/get_all_roles", methods=['POST'])
@cross_origin()
def get_all_roles():
	roles = [dict(id=role.id, role=role.role, description=role.description) for role in dbo.sess.query(Role).all()]	
	return jsonify(dict(status='success', roles=roles))


'''
Get all roles for a user
'''
@ori.route("/get_roles/<_id>", methods=['POST'])
@cross_origin()
def get_user_roles(_id):
	try:
		user = dbo.sess.query(User).filter_by(_id=_id).one()
		roles = [dict(id=role.id, role=role.role) for role in user.roles]	
		return jsonify(dict(status='success', roles=roles))
	except:
		return jsonify(dict(status='error', msg="Something went wrong"))


'''
Update an existing user defined role
'''
@ori.route("/update_role/<orole>", methods=['POST'])
@cross_origin()
def update_role(orole):
	role=req.args.get('role', None)
	description=req.args.get('description', '')

	#check if role name is set
	if role == None:
		return jsonify(dict(status='error', msg='there is no role name in your request'))

	#ensure role is alphanumeric with underscores allowed only
	if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', role) == None:
		return jsonify(dict(status='error', msg='the role includes illegal characters'))	

	#description validation
	if re.search(r'([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]+)', description) == None:
		return jsonify(dict(status='error', msg='the description includes illegal characters'))	

	#clean role and description
	role = role.strip().replace(' ', '_').lower()
	description = description.strip()

	#check if the role exists
	if len(dbo.sess.query(Role).filter_by(role=orole).all()) != 1:
		return jsonify(dict(status='error', msg='the role you want to update does not exists'))

	draft_role = dbo.sess.query(Role).filter_by(role=orole).one()

	#stop edits of the base roles
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
@ori.route("/delete_role/<role>", methods=['DELETE'])
@cross_origin()
def delete_role(role):
	#check if the role exists
	if len(dbo.sess.query(Role).filter_by(role=role).all()) != 1:
		return jsonify(dict(status='error', msg='the role you want to delete does not exists'))

	#instantiate role
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

	try:
		role = dbo.sess.query(Role).filter_by(role=orole).all()
		if len(role) == 0:
			return jsonify(dict(status='error', msg='this role does not exist'))

		user = dbo.sess.query(User).filter_by(_id=_id).one()
		if orole in [_.role for _ in user.roles]:
			return jsonify(dict(status='error', msg='this role has already been assigned'))

		#continue if assignment is not set yet
		role = dbo.sess.query(Role).filter_by(role=orole).one()
		user.roles.append(role)
		dbo.sess.commit()
		return jsonify(dict(status=f'role of {orole} successfully assgned to {_id}'))
	except Exception as e:
		return jsonify(dict(status='error', msg=f'unknown. the user may not exist {e}'))

'''
Remove Role from a User
'''
@ori.route("/remove_role_from_user/<_id>/<role>", methods=['DELETE'])
@cross_origin()
def remove_role(_id, role):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	role = dbo.sess.query(Role).filter_by(role=role).one()
	user.roles.remove(role)
	dbo.sess.commit()
	return jsonify(dict(status='deleted'))

'''
Remove all Roles for a particular User
'''
@ori.route("/remove_all_roles_from_user/<_id>", methods=['POST'])
@cross_origin()
def remove_all_user_roles(_id):
	user = dbo.sess.query(User).filter_by(_id=_id).one()
	if user.id != 1:
		user.roles = []
		dbo.sess.commit()
	return jsonify(dict(status='deleted'))

'''
Flush all User Roles
'''
@ori.route("/flush_user_roles", methods=['POST'])
@cross_origin()
def flush_user_roles():
	with dbo.engine.connect() as con:
		con.execute(text('''
			DELETE FROM users_roles 
			WHERE id > 1
		'''))
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
	#validate module name
	if re.search(r'([a-zA-Z]+)([a-zA-Z0-9_]+)', name) == None:
		return jsonify(dict(status='error', msg='the module includes illegal characters'))	

	#validate module description
	if re.search(r'([a-zA-Z0-9 ]+)([a-zA-Z0-9_. -]+)', description) == None:
		return jsonify(dict(status='error', msg='the description includes illegal characters'))	

	#instantiate module
	module = Module()
	module.module = name.strip().replace(' ', '_').lower()
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
	successful = [] #container for modules that successfully get created
	failed = [] #container for modules that fail to create - usually coz they already exist

	for module in modules:
		#validate module names
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

	return jsonify(dict(status=f'{module.capitalize()} successfully removed'))

'''
Removes all modules at once!
'''
@ori.route("/flush_modules", methods=['POST'])
@cross_origin()
def flush_modules():
	with dbo.engine.connect() as con:
		con.execute(text('''
			DELETE FROM modules
		'''))
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
	
	with dbo.engine.connect() as con:
		mrs = con.execute(text(f'''
			SELECT mr.id, mr.module_id, mr.role_id
			FROM modules_roles AS mr 
				LEFT JOIN modules AS m ON mr.module_id=m.id 
				LEFT JOIN roles AS r ON mr.role_id=r.id
			WHERE LOWER(m.module)='{module}' AND LOWER(r.role)='{role}'
		''')).fetchall()

	try:
		with dbo.engine.connect() as con:
			omodule = con.execute(text(f"SELECT * FROM modules WHERE LOWER(module)='{module}'")).fetchone()
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
	
	with dbo.engine.connect() as con:
		mus = con.execute(text(f'''
			SELECT mu.id, mu.module_id, mu.user_id
			FROM modules_users AS mu 
				LEFT JOIN modules AS m ON mu.module_id=m.id 
				LEFT JOIN users AS u ON mu.user_id=u.id
			WHERE LOWER(m.module)='{module}' AND u._id='{_id}'
		''')).fetchall()

	try:
		with dbo.engine.connect() as con:
			omodule = con.execute(text(f"SELECT * FROM modules WHERE LOWER(module)='{module}'")).fetchone()
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
	with dbo.engine.connect() as con:
		module = con.execute(text(f"SELECT * FROM modules WHERE LOWER(module)='{module}'")).fetchone()
		con.execute(text(f'''
			DELETE FROM modules_roles WHERE module_id='{module.id}'
		'''))	
		return jsonify(dict(status='success'))

'''
Remove all permissions in the modules_roles table
'''
@ori.route("/flush_role_permissions", methods=['POST'])
@cross_origin()
def flush_role_permissions():
	with dbo.engine.connect() as con:
		con.execute(text('''
			DELETE FROM modules_roles
		'''))	
		return jsonify(dict(status='success'))

'''
Remove user permissions for a particular module
'''
@ori.route("/remove_user_permissions/<module>", methods=['POST'])
@cross_origin()
def remove_user_permissions(module):
	with dbo.engine.connect() as con:
		module = con.execute(text(f"SELECT * FROM modules WHERE LOWER(module)='{module}'")).fetchone()
		con.execute(text(f'''
			DELETE FROM modules_users WHERE module_id='{module.id}'
		'''))	
		return jsonify(dict(status='success'))

'''
Remove all permissions in the modules_users table
'''
@ori.route("/flush_user_permissions", methods=['POST'])
@cross_origin()
def flush_user_permissions():
	with dbo.engine.connect() as con:
		con.execute(text('''
			DELETE FROM modules_users
		'''))	
		return jsonify(dict(status='success'))
