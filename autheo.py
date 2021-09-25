from flask import Flask, jsonify
from flask_cors import CORS
from waitress import serve

autheo = Flask(__name__)
CORS(autheo)

#import controllers
from controllers.authentication import ent


#register controllers
autheo.register_blueprint(ent)


@autheo.route('/')
def index():
	return jsonify(dict(status= 'alive'))

if __name__ == '__main__':
	#autheo.run(port=8800, host='0.0.0.0', debug=True)
	serve(autheo, port=8800, host='0.0.0.0')