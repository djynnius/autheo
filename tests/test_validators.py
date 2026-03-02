from validators.validators import (
    validate_username, validate_email, validate_password,
    validate_role_name, validate_description, validate_permission
)


class TestValidateUsername:
    def test_valid_username(self):
        valid, msg = validate_username('johndoe1')
        assert valid is True
        assert msg is None

    def test_short_username(self):
        valid, msg = validate_username('joe')
        assert valid is False
        assert 'less than 8' in msg

    def test_starts_with_number(self):
        valid, msg = validate_username('1johndoe')
        assert valid is False

    def test_empty_username(self):
        valid, msg = validate_username('')
        assert valid is False

    def test_none_username(self):
        valid, msg = validate_username(None)
        assert valid is False


class TestValidateEmail:
    def test_valid_email(self):
        valid, msg = validate_email('john@example.com')
        assert valid is True

    def test_invalid_email(self):
        valid, msg = validate_email('notanemail')
        assert valid is False

    def test_empty_email(self):
        valid, msg = validate_email('')
        assert valid is False

    def test_none_email(self):
        valid, msg = validate_email(None)
        assert valid is False


class TestValidatePassword:
    def test_valid_password(self):
        valid, msg = validate_password('Test1234!')
        assert valid is True

    def test_short_password(self):
        valid, msg = validate_password('Te1!')
        assert valid is False
        assert 'less than 8' in msg

    def test_no_uppercase(self):
        valid, msg = validate_password('test1234!')
        assert valid is False

    def test_no_special(self):
        valid, msg = validate_password('Test12345')
        assert valid is False

    def test_empty_password(self):
        valid, msg = validate_password('')
        assert valid is False

    def test_none_password(self):
        valid, msg = validate_password(None)
        assert valid is False


class TestValidateRoleName:
    def test_valid_role(self):
        valid, msg = validate_role_name('editor')
        assert valid is True

    def test_invalid_role(self):
        valid, msg = validate_role_name('ed!tor')
        assert valid is False

    def test_empty_role(self):
        valid, msg = validate_role_name('')
        assert valid is False


class TestValidateDescription:
    def test_valid_description(self):
        valid, msg = validate_description('A valid description')
        assert valid is True

    def test_invalid_description(self):
        valid, msg = validate_description('bad<script>')
        assert valid is False

    def test_empty_description(self):
        valid, msg = validate_description('')
        assert valid is False


class TestValidatePermission:
    def test_valid_permissions(self):
        for i in range(8):
            valid, msg = validate_permission(i)
            assert valid is True

    def test_out_of_range(self):
        valid, msg = validate_permission(8)
        assert valid is False

    def test_negative(self):
        valid, msg = validate_permission(-1)
        assert valid is False

    def test_non_numeric(self):
        valid, msg = validate_permission('abc')
        assert valid is False
