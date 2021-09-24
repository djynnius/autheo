from flask import Flask, jsonify

autheo = Flask(__name__)

#import controllers
from controllers.authentication import ent


#register controllers
autheo.register_blueprint(ent)

@autheo.route('/')
def index():
	return jsonify(dict(status= 'alive'))

if __name__ == '__main__':
	autheo.run(port=8800, host='0.0.0.0', debug=True)