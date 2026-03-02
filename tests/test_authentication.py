import json


def signup_user(client, username='testuser1', email='testuser@example.com', password='Test1234!'):
    return client.post('/ent/signup', data=dict(
        username=username, email=email, password=password
    ))


class TestSignup:
    def test_signup_with_username_and_email(self, client):
        resp = signup_user(client)
        data = json.loads(resp.data)
        assert resp.status_code == 201
        assert data['status'] == 'success'
        assert data['message'] == 'user created'
        assert data['data']['_id'] is not None

    def test_signup_with_username_only(self, client):
        resp = client.post('/ent/signup', data=dict(
            username='testuser1', password='Test1234!'
        ))
        assert resp.status_code == 201

    def test_signup_with_email_only(self, client):
        resp = client.post('/ent/signup', data=dict(
            email='test@example.com', password='Test1234!'
        ))
        assert resp.status_code == 201

    def test_signup_no_password(self, client):
        resp = client.post('/ent/signup', data=dict(username='testuser1'))
        data = json.loads(resp.data)
        assert resp.status_code == 400
        assert data['status'] == 'error'

    def test_signup_weak_password(self, client):
        resp = client.post('/ent/signup', data=dict(
            username='testuser1', password='weak'
        ))
        assert resp.status_code == 400

    def test_signup_short_username(self, client):
        resp = client.post('/ent/signup', data=dict(
            username='abc', password='Test1234!'
        ))
        assert resp.status_code == 400

    def test_signup_invalid_email(self, client):
        resp = client.post('/ent/signup', data=dict(
            email='notvalid', password='Test1234!'
        ))
        assert resp.status_code == 400

    def test_signup_duplicate_user(self, client):
        signup_user(client)
        resp = signup_user(client)
        data = json.loads(resp.data)
        assert resp.status_code == 409
        assert 'already exists' in data['message']

    def test_first_user_gets_admin(self, client, session):
        resp = signup_user(client)
        data = json.loads(resp.data)
        _id = data['data']['_id']

        resp2 = client.post(f'/ent/get_user/{_id}')
        user_data = json.loads(resp2.data)
        assert 'administrator' in user_data['data']['roles']
        assert 'registered' in user_data['data']['roles']

    def test_no_username_or_email(self, client):
        resp = client.post('/ent/signup', data=dict(password='Test1234!'))
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client):
        signup_user(client)
        resp = client.post('/ent/login', data=dict(
            username='testuser1', password='Test1234!'
        ))
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['status'] == 'success'
        assert data['data']['token'] is not None
        assert data['data']['_id'] is not None

    def test_login_wrong_password(self, client):
        signup_user(client)
        resp = client.post('/ent/login', data=dict(
            username='testuser1', password='WrongPass1!'
        ))
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post('/ent/login', data=dict(
            username='noone123', password='Test1234!'
        ))
        assert resp.status_code == 401

    def test_login_returns_roles(self, client):
        signup_user(client)
        resp = client.post('/ent/login', data=dict(
            username='testuser1', password='Test1234!'
        ))
        data = json.loads(resp.data)
        assert 'roles' in data['data']

    def test_login_no_handle(self, client):
        resp = client.post('/ent/login', data=dict(password='Test1234!'))
        assert resp.status_code == 400


class TestLogout:
    def test_logout_success(self, client):
        resp = signup_user(client)
        _id = json.loads(resp.data)['data']['_id']
        resp = client.post(f'/ent/logout/{_id}')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['message'] == 'logged out'

    def test_logout_nonexistent(self, client):
        resp = client.post('/ent/logout/nonexistent_id')
        assert resp.status_code == 404


class TestUserManagement:
    def test_get_users(self, client):
        signup_user(client)
        resp = client.get('/ent/get_users')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['data']['users']) == 1

    def test_get_user(self, client):
        resp = signup_user(client)
        _id = json.loads(resp.data)['data']['_id']
        resp = client.post(f'/ent/get_user/{_id}')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['data']['_id'] == _id

    def test_get_user_not_found(self, client):
        resp = client.post('/ent/get_user/fake_id')
        assert resp.status_code == 404

    def test_delete_user(self, client):
        # First user is superuser, create a second
        signup_user(client, username='firstusr1', email='first@example.com')
        resp = signup_user(client, username='secondusr', email='second@example.com')
        _id = json.loads(resp.data)['data']['_id']
        resp = client.delete(f'/ent/delete_user/{_id}')
        assert resp.status_code == 200

    def test_delete_superuser_blocked(self, client):
        resp = signup_user(client)
        _id = json.loads(resp.data)['data']['_id']
        resp = client.delete(f'/ent/delete_user/{_id}')
        data = json.loads(resp.data)
        assert resp.status_code == 400
        assert 'superuser' in data['message']

    def test_flush_users(self, client):
        signup_user(client, username='firstusr1', email='first@example.com')
        signup_user(client, username='secondusr', email='second@example.com')
        resp = client.delete('/ent/flush_users')
        assert resp.status_code == 200

        resp = client.get('/ent/get_users')
        data = json.loads(resp.data)
        # Only superuser remains
        assert len(data['data']['users']) == 1

    def test_reset_password(self, client):
        resp = signup_user(client)
        _id = json.loads(resp.data)['data']['_id']
        resp = client.put(f'/ent/reset_password/{_id}', data=dict(
            password='NewPass1!'
        ))
        assert resp.status_code == 200

    def test_verify_user(self, client):
        resp = signup_user(client)
        _id = json.loads(resp.data)['data']['_id']
        resp = client.put(f'/ent/verify/{_id}')
        assert resp.status_code == 200
