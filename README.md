# Autheo v3

A developer-ready authentication and authorization scaffold built with Flask, SQLAlchemy, PyJWT, and bcrypt.

## Features

- **Multi-database support**: SQLite (default), PostgreSQL, MySQL, MariaDB, DuckDB
- **JWT authentication**: Per-user secrets, configurable token expiry
- **Role-based access control (RBAC)**: Assign roles to users, 3 built-in roles
- **Unix-style permissions**: Module-level permissions (0-7) for roles and individual users
- **Consistent API**: Standard JSON response envelope with proper HTTP status codes
- **Services architecture**: Clean separation of HTTP handlers, business logic, and data access
- **Test suite**: 84 tests covering authentication, authorization, and validation

## Quick Start

```bash
# Clone and setup
cd autheo
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Configure (optional - defaults to SQLite)
cp .env.example .env
# Edit .env as needed

# Initialize database and seed default roles
python seed.py

# Start the server
python autheo.py
```

Verify at `http://0.0.0.0:8800`:
```json
{"status": "success", "message": "autheo v3 is alive!"}
```

## Running Tests

```bash
pytest tests/ -v
```

## Configuration

All settings are via environment variables (or `.env` file):

| Variable | Default | Description |
|---|---|---|
| `AUTHEO_DB_BACKEND` | `sqlite` | Database: sqlite, postgres, mysql, mariadb, duckdb |
| `AUTHEO_DB_HOST` | `localhost` | Database host |
| `AUTHEO_DB_PORT` | *(auto)* | Database port (5432/3306 auto-detected) |
| `AUTHEO_DB_NAME` | `autheo` | Database name |
| `AUTHEO_DB_USER` | | Database user |
| `AUTHEO_DB_PASSWORD` | | Database password |
| `AUTHEO_DB_PATH` | `dbs/autheo.db` | File path for SQLite/DuckDB |
| `AUTHEO_JWT_EXPIRY_DAYS` | `7` | JWT token expiry in days |
| `AUTHEO_PORT` | `8800` | Server port |
| `AUTHEO_HOST` | `0.0.0.0` | Server host |
| `AUTHEO_DEBUG` | `true` | Debug mode (uses Flask dev server; false uses Waitress) |

## Database Setup

### SQLite (default)
No configuration needed. Database file created automatically at `dbs/autheo.db`.

### PostgreSQL
```bash
AUTHEO_DB_BACKEND=postgres
AUTHEO_DB_HOST=localhost
AUTHEO_DB_PORT=5432
AUTHEO_DB_NAME=autheo
AUTHEO_DB_USER=myuser
AUTHEO_DB_PASSWORD=mypassword
```
Install driver: `pip install psycopg2-binary`

### MySQL / MariaDB
```bash
AUTHEO_DB_BACKEND=mysql
AUTHEO_DB_HOST=localhost
AUTHEO_DB_PORT=3306
AUTHEO_DB_NAME=autheo
AUTHEO_DB_USER=myuser
AUTHEO_DB_PASSWORD=mypassword
```
Install driver: `pip install pymysql`

### DuckDB
```bash
AUTHEO_DB_BACKEND=duckdb
AUTHEO_DB_PATH=dbs/autheo.duckdb
```
Install driver: `pip install duckdb-engine`

## API Reference

All responses follow a standard envelope:
```json
{
  "status": "success" | "error",
  "message": "description",
  "data": { ... } | null
}
```

### Authentication (`/ent`)

#### POST `/ent/signup`
Register a new user with email, username, or both.

```bash
curl -X POST http://localhost:8800/ent/signup \
  -d "username=johndoe1" \
  -d "email=john@example.com" \
  -d "password=MyPass123!"
```
**Response** (201):
```json
{"status": "success", "message": "user created", "data": {"_id": "a1b2c3..."}}
```

#### POST `/ent/login`
Authenticate with username or email.

```bash
curl -X POST http://localhost:8800/ent/login \
  -d "username=johndoe1" \
  -d "password=MyPass123!"
```
**Response** (200):
```json
{
  "status": "success",
  "message": "authenticated",
  "data": {
    "_id": "a1b2c3...",
    "username": "johndoe1",
    "email": "john@example.com",
    "token": "eyJ...",
    "roles": ["administrator", "registered"],
    "permissions": [{"module": "news", "permissions": 7}],
    "since": "2024-01-01T00:00:00",
    "last_login": null
  }
}
```

#### POST/GET `/ent/logout/<_id>`
Logout user and invalidate token.

#### POST/GET `/ent/get_users`
Get all users.

#### POST `/ent/get_user/<_id>`
Get details for a specific user including roles and permissions.

#### DELETE `/ent/delete_user/<_id>`
Delete a user (superuser protected).

#### DELETE `/ent/flush_users`
Delete all users except superuser.

#### PUT `/ent/reset_password/<_id>`
Update user password.

```bash
curl -X PUT http://localhost:8800/ent/reset_password/a1b2c3... \
  -d "password=NewPass456!"
```

#### PUT `/ent/verify/<_id>`
Mark user as verified.

### Authorization (`/ori`)

#### Roles

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ori/create_role/<role>/<description>` | Create a new role |
| POST | `/ori/get_all_roles` | List all roles |
| POST | `/ori/get_users_for_role/<role>` | Get users with a role |
| POST | `/ori/get_roles/<_id>` | Get roles for a user |
| POST | `/ori/update_role/<role>?role=<new>&description=<desc>` | Update a role (base roles protected) |
| DELETE | `/ori/delete_role/<role>` | Delete a role (base roles protected) |

#### User-Role Assignment

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ori/assign_role/<_id>/<role>` | Assign role to user |
| DELETE | `/ori/remove_role_from_user/<_id>/<role>` | Remove role from user |
| POST | `/ori/remove_all_roles_from_user/<_id>` | Remove all roles (superuser protected) |
| POST | `/ori/flush_user_roles` | Clear all user-role assignments |

#### Modules

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ori/register_module/<name>/<description>` | Register a module |
| POST | `/ori/register_modules?1=News&2=Blog` | Bulk register modules |
| POST | `/ori/remove_module/<module>` | Remove a module |
| POST | `/ori/flush_modules` | Remove all modules |
| POST | `/ori/get_modules` | List all modules |

#### Permissions

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ori/set_role_permissions/<module>/<role>/<permission>` | Set role permissions on module |
| POST | `/ori/set_user_permissions/<module>/<_id>/<permission>` | Set user permissions on module |
| POST | `/ori/remove_role_permissions/<module>` | Remove role permissions for module |
| POST | `/ori/flush_role_permissions` | Clear all role permissions |
| POST | `/ori/remove_user_permissions/<module>` | Remove user permissions for module |
| POST | `/ori/flush_user_permissions` | Clear all user permissions |

## Permissions System

Autheo uses Unix-style permission values (0-7):

| Value | Access |
|---|---|
| 0 | No permission |
| 1 | Read only |
| 2 | Write/Edit (no read) |
| 3 | Read + Write |
| 4 | Execute/Delete only |
| 5 | Read + Execute/Delete |
| 6 | Write + Execute/Delete (no read) |
| 7 | Full (Read + Write + Execute/Delete) |

Permissions can be set at the role level (inherited by all users with that role) or the user level (specific to one user). When both exist, the higher permission value wins.

### OAuth (`/ope`)

OAuth login via Google, GitHub, and Discord. Enable a provider by setting its `CLIENT_ID` and `CLIENT_SECRET` environment variables.

#### Setup

```bash
# In .env
AUTHEO_GOOGLE_CLIENT_ID=your-google-client-id
AUTHEO_GOOGLE_CLIENT_SECRET=your-google-client-secret
AUTHEO_OAUTH_REDIRECT_BASE=http://localhost:8800
```

Set each provider's OAuth redirect URI to `{OAUTH_REDIRECT_BASE}/ope/callback/{provider}` (e.g. `http://localhost:8800/ope/callback/google`).

#### Flow

1. Client calls `GET /ope/login/google` and gets a 302 redirect to Google's consent screen
2. User authorizes, Google redirects to `GET /ope/callback/google?code=...`
3. Autheo exchanges the code for an access token, fetches the user profile, and returns a JWT

On first OAuth login, a local user is auto-created (verified, no password). If the provider email matches an existing local user, the OAuth account is linked instead.

#### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/ope/providers` | List enabled OAuth providers |
| GET | `/ope/login/<provider>` | Redirect to provider's authorization URL |
| GET | `/ope/callback/<provider>?code=...` | Exchange code and return JWT |

#### Example

```bash
# Check which providers are enabled
curl http://localhost:8800/ope/providers

# Start OAuth flow (returns 302)
curl -v http://localhost:8800/ope/login/google
```

## Migration from v2

Key changes in v3:
- All API responses now use a standard envelope with `status`, `message`, and `data` fields
- HTTP status codes are now semantic (201 for created, 400 for errors, 401 for auth failures, 404 for not found, 409 for conflicts)
- Boolean fields (`loggedin`, `verified`) now return `true`/`false` instead of `"yes"`/`"no"`
- Database configuration via environment variables instead of editing source code
- `dbo.py` replaced by `seed.py` for initialization
- All SQL injection vulnerabilities fixed (ORM-only queries)
