# autheo
A simple authentication and authorization system
Built with Flask, SQLAlchemy, PyJWT, Waitress

## For first setup
```bash
#BASH
cd autheo/models
python3 dbo.py #instantiates database
mv autheo.py ../dbs/ #optional if configured to use SQLite3

cd .. #return to home directory
python3 autheo.py #start the flask app

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
