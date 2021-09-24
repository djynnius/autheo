from flask import Blueprint, jsonify

ent = Blueprint('authentication', __name__, url_prefix='/ent')

@ent.route("/signup")
def signup():
	return jsonify(dict(status='success'))