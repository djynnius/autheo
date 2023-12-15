# autheo
A simple authentication and authorization system
Built with Flask, SQLAlchemy, PyJWT, Waitress

## For first setup
```bash
#BASH

#setting up the virtual environment
cd autheo
python3 -m venv env
source env/bin/activate
pip install --upgrade-pip
pip install -r requirements.txt --user

#if you need to setup DB other than the autheo.db SQLite instance
#edit the config in autheo/models/dbo.py
#then run ``python dbo.py`` to instantiate DB before proceeding

#autheo also runs out the box on port 8800.
#You can modify as you deem fit

```

To start the server
```bash
python autheo.py

#if you test the url 0.0.0.0:8800 you should get a message
#autheo is alive!
```

The rest involves calling APIs

### Signing up with JavaScript

You can signup using username/handle

```javascript
//JavaScript
data = new FormData()
data.append('username', 'oluseyi.emeka')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/signup`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

or using email

```javascript
//JavaScript
data = new FormData()
data.append('email', 'oemeka@gmail.com')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/signup`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

or using both username and email

```javascript
//JavaScript
data = new FormData()
data.append('username', 'oluseyi.emeka')
data.append('email', 'oemeka@gmail.com')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/signup`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

### Loging in with JavaScript

You can login with username/password or email/password combination depending on what you setup

```javascript
//JavaScript
data = new FormData()
data.append('username', 'oluseyi.emeka')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/login`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

### Loging out with JavaScript

logout using the \_id property

```javascript
//JavaScript
fetch(`https://myautheoserver.io/ent/logout/c68f463cx0d7f823df95y8c50943e651`) 
	.then(r=>r.json())
	.then(r=>console.log(r))

```

## Other API calls

### Authentication

Request to get all users
```javascript
fetch(`https://myautheoserver.io/ent/get_users`, {method:'POST'}) 
```

Get details for a particular user
```javascript
//last part or URL is user id
fetch(`https://myautheoserver.io/ent/get_user/c68f463cx0d7f823df95y8c50943e651`, {method:'POST'}) 
```

Delete a particular user
```javascript
fetch(`https://myautheoserver.io/ent/delete_user/c68f463cx0d7f823df95y8c50943e651`, {method:'DELETE'})
```

Delete all users
```javascript
fetch(`https://myautheoserver.io/ent/flush_users`, {method:'DELETE'})
```

Reset user password
```javascript
data = new FormData()
data.append('password', 'NewPassword_2022!')
fetch(`https://myautheoserver.io/ent/reset_password/c68f463cx0d7f823df95y8c50943e651`, {method:'PUT', body: data})
```

Verify a user account example by phone or email
```javascript
fetch(`https://myautheoserver.io/ent/verify/c68f463cx0d7f823df95y8c50943e651`, {method:'PUT'})
```

### Authorization

Create a new role
```javascript
fetch(`https://myautheoserver.io/ori/create_role/accountant/manages the financial transactions`, {method: 'POST'})
```

Get all roles
```javascript
fetch(`https://myautheoserver.io/ori/get_all_roles`, {method: 'POST'})
```

Get all roles for a user
```javascript
fetch(`https://myautheoserver.io/ori/get_roles/c68f463cx0d7f823df95y8c50943e651`, {method: 'POST'})
```

Update an existing user defined role
```javascript
fetch(`https://myautheoserver.io/ori/update_role/accountant?role=finance_manager&description=head of financial transactions`, {method: 'POST'})
```

Delete existing user defined role
```javascript
fetch(`https://myautheoserver.io/ori/delete_role/accountant`, {method: 'DELETE'})
```

Assign Role to a User
```javascript
fetch(`https://myautheoserver.io/ori/assign_role/c68f463cx0d7f823df95y8c50943e651/accountant`, {method: 'POST'})
```


Remove Role from a User
```javascript
fetch(`https://myautheoserver.io/ori/remove_role_from_user/c68f463cx0d7f823df95y8c50943e651/accountant`, {method: 'POST'})
```

Remove all Roles for a particular User
```javascript
fetch(`https://myautheoserver.io/ori/remove_all_roles_from_user/c68f463cx0d7f823df95y8c50943e651`, {method: 'POST'})
```


Flush all user role assignments
```javascript
fetch(`https://myautheoserver.io/ori/flush_user_roles`, {method: 'POST'})
```

Register a module
```javascript
fetch(`https://myautheoserver.io/ori/register_module/news/current events local and international`, {method: 'POST'})
```

Register multiple modules using aruments in url string 
```javascript
//Does not include description
fetch(`https://myautheoserver.io/ori/register_modules?1=news&2=gallery&3=blog`, {method: 'POST'})
```

Remove a module
```javascript
fetch(`https://myautheoserver.io/ori/remove_module/news`, {method: 'POST'})
```
Removes all modules at once!
```javascript
fetch(`https://myautheoserver.io/ori/flush_modules`, {method: 'POST'})
```

View all modules
```javascript
fetch(`https://myautheoserver.io/ori/get_modules`, {method: 'POST'})
```

##### Add priviledges to a module for a role so everyone with that role inherits those permissions
The Unix standard is used
- 0 = no permission, 
- 1 = Basic eg read only
- 2 = Edit/Write priviledged without read priviledges
- 3 = Read and Write access
- 4 = Highest single priviledge eg Execute, Delete
- 5 = Read and Execute/Delete
- 6 = Write and Execute/Delete but not Read
- 7 = Full priviledges ie Read Edit/Write and Execute/Delete

```javascript
//set read and execute
fetch(`https://myautheoserver.io/ori/set_role_permissions/news/accountant/5`, {method: 'POST'})
```


Set permissions that are specific to users
```javascript
//set read and edit permissions
fetch(`https://myautheoserver.io/ori/set_user_permissions/news/c68f463cx0d7f823df95y8c50943e651/3`, {method: 'POST'})
```

Remove all role permissions for a particular module
```javascript
fetch(`https://myautheoserver.io/ori/remove_role_permissions/news`, {method: 'POST'})
```

Remove all permissions in the modules_roles table
```javascript
fetch(`https://myautheoserver.io/ori/flush_role_permissions`, {method: 'POST'})
```


Remove user permissions for a particular module
```javascript
fetch(`https://myautheoserver.io/ori/remove_user_permissions/news`, {method: 'POST'})
```

Remove all permissions in the modules_users table
```javascript
fetch(`https://myautheoserver.io/ori/flush_user_permissions`, {method: 'POST'})
```
