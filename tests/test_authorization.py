import json


def signup_user(client, username='testuser1', email='testuser@example.com', password='Test1234!'):
    resp = client.post('/ent/signup', data=dict(
        username=username, email=email, password=password
    ))
    return json.loads(resp.data)['data']['_id']


class TestRoles:
    def test_create_role(self, client):
        resp = client.post('/ori/create_role/editor/Content editor role')
        data = json.loads(resp.data)
        assert resp.status_code == 201
        assert data['data']['role_id'] is not None

    def test_create_duplicate_role(self, client):
        client.post('/ori/create_role/editor/Content editor role')
        resp = client.post('/ori/create_role/editor/Content editor role')
        assert resp.status_code == 409

    def test_create_role_invalid_name(self, client):
        resp = client.post('/ori/create_role/bad!name/description here')
        assert resp.status_code == 400

    def test_get_all_roles(self, client):
        resp = client.post('/ori/get_all_roles')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        # 3 default roles
        assert len(data['data']['roles']) == 3

    def test_update_role(self, client):
        client.post('/ori/create_role/editor/Content editor role')
        resp = client.post('/ori/update_role/editor?role=senior_editor&description=Senior editor role')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['data']['role_id'] is not None

    def test_update_base_role_blocked(self, client):
        resp = client.post('/ori/update_role/administrator?role=admin&description=New admin')
        assert resp.status_code == 400

    def test_delete_role(self, client):
        client.post('/ori/create_role/editor/Content editor role')
        resp = client.delete('/ori/delete_role/editor')
        data = json.loads(resp.data)
        assert resp.status_code == 200

    def test_delete_base_role_blocked(self, client):
        resp = client.delete('/ori/delete_role/administrator')
        assert resp.status_code == 400

    def test_delete_role_commits(self, client):
        """Tests bug #4 fix: delete_role now commits properly."""
        client.post('/ori/create_role/temp_role/Temporary role')
        client.delete('/ori/delete_role/temp_role')
        resp = client.post('/ori/get_all_roles')
        data = json.loads(resp.data)
        role_names = [r['role'] for r in data['data']['roles']]
        assert 'temp_role' not in role_names


class TestUserRoles:
    def test_assign_role(self, client):
        _id = signup_user(client)
        client.post('/ori/create_role/editor/Content editor')
        resp = client.post(f'/ori/assign_role/{_id}/editor')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert 'assigned' in data['message']  # Fixes typo "assgned"

    def test_assign_duplicate_role(self, client):
        _id = signup_user(client)
        client.post(f'/ori/assign_role/{_id}/registered')
        resp = client.post(f'/ori/assign_role/{_id}/registered')
        assert resp.status_code == 409

    def test_get_user_roles(self, client):
        _id = signup_user(client)
        resp = client.post(f'/ori/get_roles/{_id}')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        role_names = [r['role'] for r in data['data']['roles']]
        assert 'registered' in role_names

    def test_get_users_for_role(self, client):
        signup_user(client)
        resp = client.post('/ori/get_users_for_role/registered')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['data']['users']) >= 1

    def test_remove_role_from_user(self, client):
        _id = signup_user(client)
        client.post('/ori/create_role/editor/Content editor')
        client.post(f'/ori/assign_role/{_id}/editor')
        resp = client.delete(f'/ori/remove_role_from_user/{_id}/editor')
        assert resp.status_code == 200

    def test_remove_all_roles(self, client):
        # First user becomes superuser, create second user for this test
        signup_user(client, username='firstusr1', email='first@test.com')
        _id = signup_user(client, username='secondusr', email='second@test.com')
        resp = client.post(f'/ori/remove_all_roles_from_user/{_id}')
        assert resp.status_code == 200

    def test_flush_user_roles(self, client):
        """Tests bug #5 fix: flush_user_roles no longer references nonexistent id column."""
        signup_user(client)
        resp = client.post('/ori/flush_user_roles')
        assert resp.status_code == 200


class TestModules:
    def test_register_module(self, client):
        resp = client.post('/ori/register_module/articles/Article management')
        data = json.loads(resp.data)
        assert resp.status_code == 201

    def test_register_duplicate_module(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/register_module/articles/Article management')
        assert resp.status_code == 409

    def test_register_modules_bulk(self, client):
        resp = client.post('/ori/register_modules?1=News&2=Blog&3=Forum')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['data']['success']) == 3
        assert len(data['data']['failed']) == 0

    def test_register_modules_some_duplicates(self, client):
        client.post('/ori/register_module/news/News module')
        resp = client.post('/ori/register_modules?1=News&2=Blog')
        data = json.loads(resp.data)
        assert 'news' in data['data']['failed']

    def test_remove_module(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/remove_module/articles')
        assert resp.status_code == 200

    def test_flush_modules(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/flush_modules')
        assert resp.status_code == 200
        resp = client.post('/ori/get_modules')
        data = json.loads(resp.data)
        assert len(data['data']['modules']) == 0

    def test_get_modules(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/get_modules')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert len(data['data']['modules']) >= 1


class TestRolePermissions:
    def test_set_role_permissions(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/set_role_permissions/articles/administrator/7')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['message'] == 'permissions updated'

    def test_update_role_permissions(self, client):
        """Tests that setting permissions twice updates rather than duplicates."""
        client.post('/ori/register_module/articles/Article management')
        client.post('/ori/set_role_permissions/articles/administrator/3')
        resp = client.post('/ori/set_role_permissions/articles/administrator/7')
        assert resp.status_code == 200

    def test_set_role_permissions_invalid_permission(self, client):
        client.post('/ori/register_module/articles/Article management')
        resp = client.post('/ori/set_role_permissions/articles/administrator/9')
        assert resp.status_code == 400

    def test_remove_role_permissions(self, client):
        client.post('/ori/register_module/articles/Article management')
        client.post('/ori/set_role_permissions/articles/administrator/7')
        resp = client.post('/ori/remove_role_permissions/articles')
        assert resp.status_code == 200

    def test_flush_role_permissions(self, client):
        client.post('/ori/register_module/articles/Article management')
        client.post('/ori/set_role_permissions/articles/administrator/7')
        resp = client.post('/ori/flush_role_permissions')
        assert resp.status_code == 200


class TestUserPermissions:
    def test_set_user_permissions(self, client):
        """Tests bugs #2/#3 fix: set_user_permissions works correctly."""
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        resp = client.post(f'/ori/set_user_permissions/articles/{_id}/5')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['message'] == 'permissions updated'

    def test_update_user_permissions(self, client):
        """Tests that setting permissions twice updates rather than duplicates."""
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        client.post(f'/ori/set_user_permissions/articles/{_id}/3')
        resp = client.post(f'/ori/set_user_permissions/articles/{_id}/7')
        assert resp.status_code == 200

    def test_remove_user_permissions(self, client):
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        client.post(f'/ori/set_user_permissions/articles/{_id}/5')
        resp = client.post('/ori/remove_user_permissions/articles')
        assert resp.status_code == 200

    def test_flush_user_permissions(self, client):
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        client.post(f'/ori/set_user_permissions/articles/{_id}/5')
        resp = client.post('/ori/flush_user_permissions')
        assert resp.status_code == 200

    def test_permissions_in_login(self, client):
        """Tests that permissions show up in login response."""
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        client.post(f'/ori/set_user_permissions/articles/{_id}/5')
        resp = client.post('/ent/login', data=dict(
            username='testuser1', password='Test1234!'
        ))
        data = json.loads(resp.data)
        assert any(p['module'] == 'articles' for p in data['data']['permissions'])

    def test_permissions_cascade_on_module_delete(self, client):
        """Tests that deleting a module cascades to permission associations."""
        _id = signup_user(client)
        client.post('/ori/register_module/articles/Article management')
        client.post(f'/ori/set_user_permissions/articles/{_id}/5')
        client.post('/ori/remove_module/articles')
        # After module deletion, login should not show articles permissions
        resp = client.post('/ent/login', data=dict(
            username='testuser1', password='Test1234!'
        ))
        data = json.loads(resp.data)
        assert not any(p['module'] == 'articles' for p in data['data']['permissions'])
