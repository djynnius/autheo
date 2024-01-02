from uuid import uuid4 as uuid

def uuidhex():
	return uuid().hex

def _email():
	return f"{uuid().hex[:5]}@noemail.xyz"

def _username():
	return f"{uuid().hex[:8]}"