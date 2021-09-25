# autheo
A simple authentication and authorization system
Built with Flask, SQLAlchemy, PyJWT, Waitress

## For first setup
```{python}
cd autheo/models
python3 dbo.py #instantiates database

```

The rest of involves calling APIs

### Signing up with JavaScript

```{javascript}
data = new FormData()
data.append('username', 'john.smith')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/signup`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

### Loging in with JavaScript

```{javascript}
data = new FormData()
data.append('username', 'john.smith')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/login`, {method: 'POST', body: data})
	.then(r=>r.json())
	.then(r=>console.log(r))

```

### Loging out with JavaScript

```{javascript}
data = new FormData()
data.append('username', 'john.smith')
data.append('password', 'Password@2021')
fetch(`https://myautheoserver.io/ent/logout/euiueiuiuissadsadadsda`) 
	.then(r=>r.json())
	.then(r=>console.log(r))

```
