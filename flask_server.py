'''
This module contains functions and code to run the Flask server hosting averi.cloud
It should be run as 'python3 flask_server.py'

Parameters:
	None
	[See FlaskConstants for more information]

Variables:
	db			Instance of DB_Handler
	wg_config	Instance of WireguardConfig
	app			Instance of Flask

Functions:
	is_logged_in
	sign_out
	mfa
	index
	login
	register
	logout
	execute
	add_device
	get_config

Flask Routes:
	[Route]			[Function]
	/				index
	/2fa			mfa
	/login			login
	/register		register
	/logout			logout
	/execute		execute
	/new_device		add_device
	/get_config		get_config
'''

from flask import Flask, render_template, redirect, request, session, url_for, send_file, Response
import secrets, requests, random, json
from constants import WireguardConstants, FlaskConstants, DeviceConstants

from db import DB_Handler
db = DB_Handler.DB_Handler()
from wireguard_handler import WireguardConfig
wg_config = WireguardConfig()

app = Flask(__name__)
app.config['SECRET_KEY'] = FlaskConstants.secret_key

def is_logged_in():
	'''
	Checks if the user is logged in

	Parameters:
		None
	
	Returns
		True if the user is logged in
		False otherwise
	'''
	return FlaskConstants.user_id_session_key in session

def sign_out():
	'''
	Logs out the user

	Parameters:
		None

	Returns:
		Redirect to index
	'''
	session.pop(FlaskConstants.user_id_session_key, None)
	return redirect(url_for('index'))

@app.route('/2fa', methods=['GET'])
def mfa():
	'''
	Generate 2FA token given a 2FA seed
	REMOVE FROM PRODUCTION - 2FA SEED IS WRITTEN TO LOGS

	Flask Methods: GET

	Parameters:
		Function:
			None
		Session:
			None
		GET/Querystring:
			2fa		The 2FA seed
		POST/Form
			N/A

	Returns:
		Current token based on 2fa seed
	'''
	import pyotp
	return pyotp.TOTP(request.args.get('2fa')).now()

@app.route('/', methods=['GET'])
def index():
	'''
	Default landing page

	Flask Methods: GET

	Parameters:
		Function:
			None
		Session:
			FlaskConstants.user_id_session_key
		GET/Querystring:
			None
		POST/Form:
			N/A

	Returns:
		main_page.html template if signed in
		redirect to login if not signed in
	'''
	if not is_logged_in():
		return redirect(url_for('login'))
	# Collect and print information about the user
	user_info = db.get_user_info(session.get(FlaskConstants.user_id_session_key, -1))
	render_dict =  {'first_name' : user_info.first_name,
					'last_name' : user_info.last_name,
					'email' : user_info.email,
					'devices' : db.get_user_devices(session.get(FlaskConstants.user_id_session_key, -1))}
	return render_template('main_page.html', **render_dict)

@app.route('/login', methods=['GET', 'POST'])
def login():
	'''
	Default landing page

	Flask Methods: GET, POST

	Parameters:
		Function:
			None
		Session:
			None
		GET/Querystring:
			None
		POST/Form:
			username	Users(Email)
			password	Users(Password) [Unhashed]
			mfa			Token generated from Users(MFASeed)

	Returns:
		GET:
			login.html template
		POST:
			Redirect to index if credentials are valid
			login_fail.html template if credentials are invalid
	'''
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		mfa_token = request.form['mfa']
		userid =  db.validate_login(username, password, mfa_token)
		if userid == -1:
			return render_template('login_fail.html')
		else:
			session[FlaskConstants.user_id_session_key] = userid
			return redirect(url_for('index'))
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	'''
	Default landing page

	Flask Methods: GET, POST

	Parameters:
		Function:
			None
		Session:
			None
		GET/Querystring:
			None
		POST/Form:
			email		Users(Email)
			password	Users(Password) [Unhashed]
			first_name	Users(FirstName)
			last_name	Users(LastName)

	Returns:
		GET:
			register.html template
		POST:
			register_success.html template on success
			register_fail.html template on failure
	'''
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		mfa_seed = db.add_user(email, password, first_name, last_name)
		if not mfa_seed:
			format_dict = {'first_name' : first_name, 'last_name' : last_name}
			return render_template('register_fail.html', **format_dict)
		else:
			format_dict = {'first_name' : first_name, 'last_name' : last_name, 'mfa_seed' : mfa_seed}
			return render_template('register_success.html', **format_dict)
	return render_template('register.html')

@app.route('/logout', methods=['GET'])
def logout():
	'''
	Default landing page

	Flask Methods: GET

	Parameters:
		Function:
			None
		Session:
			None
		GET/Querystring:
			None

	Returns:
		redirect to login if not signed in
		return signout() if signed in
	'''
	if not is_logged_in():
		return redirect(url_for('login'))
	return sign_out()

@app.route('/execute', methods=['GET', 'POST'])
def execute():
	'''
	Default landing page

	Flask Methods: GET, POST

	Parameters:
		Function:
			None
		Session:
			FlaskConstants.user_id_session_key
		GET/Querystring:
			deviceid
			uri
			method
		POST/Form:
			deviceid
			uri
			method

	Returns:
		GET:
			redirect to login if not signed in
			Content of request response performed to device on success
			execute_failure.html template on failure
		POST:
			redirect to login if not signed in
			Content of request response performed to device on success
			execute_failure.html template on failure
	'''
	try:
		if not is_logged_in():
			return redirect(url_for('login'))
		if request.method == 'POST':
			userid = session.get(FlaskConstants.user_id_session_key)
			deviceid = request.form.get('deviceid', -1)
			uri = request.form.get('uri', -1)
			method = request.form.get('method')
			# This function will return a network address or false. If we don't get a network address, it is a bad request
			network_address = db.validate_request(userid, deviceid, uri, method)
			if not network_address:
				return render_template('execute_failure.html')
			else:
				target = 'http://[' + network_address + ']:' + str(DeviceConstants.listen_port) + uri
				return requests.post(target).content
		if request.method == 'GET':
			userid = session.get(FlaskConstants.user_id_session_key, -1)
			deviceid = request.args.get('deviceid', -1)
			uri = request.args.get('uri')
			method = request.args.get('method')
			# This function will return a network address or false. If we don't get a network address, it is a bad request
			network_address = db.validate_request(userid, deviceid, uri, method)
			if not network_address:
				return render_template('execute_failure.html')
			else:
				if method == 'GET':
					target = 'http://[' + network_address + ']:' + str(DeviceConstants.listen_port) + uri
					return requests.get(target).content
				elif method == 'STRM':
					stream = requests.get('http://[' + network_address + ']:' + str(DeviceConstants.stream_port) + uri, stream=True)
					block_size = int(0.1*1024*1024)
					return Response(stream.iter_content(chunk_size=block_size), content_type=stream.headers['Content-Type'])
				else:
					return render_template('execute_failure.html')
		return render_template('execute_failure.html')
	except:
		return render_template('execute_failure.html')

@app.route('/new_device', methods=['GET', 'POST'])
def add_device():
	'''
	Default landing page

	Flask Methods: GET, POST

	Parameters:
		Function:
			None
		Session:
			FlaskConstants.user_id_session_key
		GET/Querystring:
			None
		POST/Form:
			name

	Returns:
		GET:
			redirect to login if not signed in
			add_device.html template
		POST:
			redirect to login if not signed in
			add_device_success.html template on success
			add_device_failure.html template on failure
	'''
	if not is_logged_in():
		return redirect(url_for('login'))
	if request.method == 'POST':
		name = request.form['name']
		network_address = wg_config.add_client()
		tokenOne = random.randint(1,2048)
		tokenOneVal = db.get_token_from_id(tokenOne)
		tokenTwo = random.randint(1,2048)
		tokenTwoVal = db.get_token_from_id(tokenTwo)
		tokenThree = random.randint(1,2048)
		tokenThreeVal = db.get_token_from_id(tokenThree)
		if db.add_device(session.get(FlaskConstants.user_id_session_key), name, network_address, network_address.replace(':', ''), tokenOne, tokenTwo, tokenThree):
			device_dict = {'name' : name, 'network_address' : network_address, 'tokenOne' : tokenOneVal, 'tokenTwo' : tokenTwoVal, 'tokenThree' : tokenThreeVal}
			return render_template('add_device_success.html', **device_dict)
		else:
			device_dict = {'name' : name}
			return render_template('add_device_failure.html', **device_dict)
	return render_template('add_device.html')


# Parameters
# tokenOne - word submitted by user
# tokenTwo - word submitted by user
# tokenThree - word submitted by user
# capabilities - Each capabality is a JSON dictionary containing the uri, string, and method. Multiple capabilities are split with '|'. Example shown below
# {"uri": "/turnoff", "string": "Turn off the device", "method": "POST"}|{"uri": "/turnon", "string": "Turn on the device", "method": "POST"}|{"uri": "status", "string": "Get the current status", "method": "GET"}

######curl example##################
#curl --location --request POST 'averi.cloud:5000/get_config' \
#--form 'tokenOne="vague"' \
#--form 'tokenTwo="soldier"' \
#--form 'tokenThree="noodle"' \
#--form 'capabilities="{\"uri\": \"/turnoff\", \"string\": \"Turn off the device\", \"method\": \"POST\"}|{\"uri\": \"/turnon\", \"string\": \"Turn on the device\", \"method\": \"POST\"}|{\"uri\": \"status\", \"string\": \"Get the current status\", \"method\": \"GET\"}"' \
#-o config.conf 
################
@app.route('/get_config', methods=['POST'])
def get_config():
	'''
	Default landing page

	Flask Methods: POST

	Parameters:
		Function:
			None
		Session:
			None
		POST/Form:
			tokenOne		Token representing tokenID in DeviceWireguardConfigs(TokenOne)
			tokenTwo		Token representing tokenID in DeviceWireguardConfigs(TokenTwo)
			tokenThree		Token representing tokenID in DeviceWireguardConfigs(TokenThree)
			capabilities	See information below

	Returns:
		404 on invalid tokens
		Wireguard config file on success

	Capabilities format:
		List of JSON dictionaries separated by |
		Dictionaries must have the following:
			uri			representing DeviceEndpoints(EndpointURI)
			string		representing DeviceEndpoints(EndpointString)
			method		representing Method
		Note that uri should start with /
		Example:
			{"uri": "/turnoff", "string": "Turn off the device", "method": "POST"}|{"uri": "/turnon", "string": "Turn on the device", "method": "POST"}|{"uri": "status", "string": "Get the current status", "method": "GET"}
			This example represents a smart switch with 3 endpoints
	'''
	try:
		tokenOne = request.form['tokenOne']
		tokenTwo = request.form['tokenTwo']
		tokenThree = request.form['tokenThree']
		capabilities = request.form['capabilities']
	except:
		return str(400)
	config_file_name, deviceid = db.get_config_file(tokenOne, tokenTwo, tokenThree)
	if not config_file_name:
		return str(404)
	for capability in capabilities.split('|'):
		capabilitydict = json.loads(capability)
		db.add_capability(deviceid, capabilitydict.get('uri'), capabilitydict.get('string'), capabilitydict.get('method'))
	db.remove_token_config_access(deviceid)
	return send_file(WireguardConstants.client_config_dir + config_file_name, as_attachment=True)
	

if __name__ == '__main__':
	import ssl
	context = ssl.SSLContext()
	# expired certs? run certbot renew and copy certs from /etc/letsencrypt/live/averi.cloud/
	# for whatever reason i cannot chown these files
	context.load_cert_chain(FlaskConstants.https_certificate_path, keyfile=FlaskConstants.https_keyfile_path)
	# want to run on port 443 for normal https without sudo? run this
	# sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 4430
	app.run(host=FlaskConstants.host, port=FlaskConstants.port, ssl_context=context, threaded=True)

