from flask import Flask
from constants import DeviceConstants

app = Flask(__name__) 

@app.route('/post_demo', methods=['POST'])
def post_demo():
	print('post_demo ran')
	return 'post_demo ran'

@app.route('/post_demo2', methods=['POST'])
def post_demo2():
	print('post_demo2 ran')
	return 'post_demo2 ran'

@app.route('/get_demo', methods=['GET'])
def get_demo():
	print('get_demo ran')
	return 'get_demo ran'

@app.route('/get_demo2', methods=['GET'])
def get_demo2():
	print('get_demo2 ran')
	return 'get_demo2 ran'

if __name__ == '__main__':
	# TODO: only listen on wg0 interface and from 'fc00::1', the virtual IP of the server
	app.run(host="::", port=DeviceConstants.listen_port)