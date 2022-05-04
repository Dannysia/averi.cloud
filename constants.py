'''
This module contains classes that contain constants

Classes:
	DeviceConstants
	DatabaseConstants
	WireguardConstants
	FlaskConstants
'''

# TODO: put this in its own file - we don't want to share credentials from constants.py with devices
class DeviceConstants:
	'''
	This class contains constants used by devices
	
	Variables:
		listen_port		The port used for general purpose GET/POST requests
		stream_port		The port used for streaming using a GET request
	'''
	listen_port = 5000
	stream_port = 8080

class DatabaseConstants:
	'''
	This class contains constants used to connect to the database
	
	Variables:
		host		The host that is hosting the database
		user		The database user to connect with (not a unix user)
		password	The password of the database user
		database	The database within MySQL that will be used
	'''
	host = 'localhost'
	user = 'web_user'
	password = 'password'
	database = 'AVERI'

class WireguardConstants:
	'''
	This class contains constants used for WireGuard configuration
	
	Variables:
		client_config_dir		Client config files are stored in this directory
		server_public_key		This is the public key of the server
								Generate this key by running the private key stored in the interface section of /etc/wireguard/wg0.conf 
								through 'echo <private key> | wg pubkey' and saving the output
		server_port				The port used for the wireguard service
		server_domain			The domain of the wireguard server
		server_config_path		The path to the server config file
		server_interface		The name of the wireguard interface on the server
		client_config_string	The template for a client config file
		server_config_string	The template for the part to be appended to the server config file
		keepalive_time			The time between keepalive packets between devices and the server
		server_vpn_ip			The IP of the wireguard server within the virtual network
		initial_client_vpn_ip	The IP for the first device
	'''
	client_config_dir = '/home/danny/client_configs/'
	# get this value from /etc/wireguard/wg0.conf on the server - run the privatekey through command 'echo <privkey> | wg pubkey' where privkey is the private key
	server_public_key = 'yjvgwIaTH1WCM59XOg6pBN+kOklf4gW39aJV6nzhCjk='
	server_port = 3411
	server_domain = 'averi.cloud'
	server_config_path = '/etc/wireguard/wg0.conf'
	server_interface = 'wg0'
	client_config_string =  '[Interface]\n' + \
							'PrivateKey = {client_private_key}\n' + \
							'Address = {client_address}\n' + \
							'\n' + \
							'[Peer]\n' + \
							'PublicKey = {server_public_key}\n' + \
							'PresharedKey = {client_preshared_key}\n' + \
							'Endpoint = {server_public_domain}:{server_port}\n' + \
							'AllowedIPs = {server_address}\n' + \
							'PersistentKeepalive = {keepalive_time}\n'
	server_config_string =  '[Peer]\n' +\
							'PublicKey = {client_public_key}\n' + \
							'PresharedKey = {client_preshared_key}\n' + \
							'AllowedIPs = {client_address}\n\n\n'
	keepalive_time = 30
	server_vpn_ip = 'fc00::1'
	initial_client_vpn_ip = 'fc00::2'

class FlaskConstants:
	'''
	This class contains constants used by the Flask server
	
	Variable:
		https_certificate_path	The path to certificate for HTTPS
		https_keyfile_path		The path to the keyfile for HTTPS
		host					The domain or IP pointing to the HTTPS server
		port					The port to run HTTPS on
								If you cannot run with root, run on a different port and forward 443 to that port
								See readme.txt for more information
		secret_key				The secret key used for cookie cryptography
		user_id_session_key		The key storing the userid in the session dictionary
	'''
	https_certificate_path = '/home/danny/cert.pem'
	https_keyfile_path = '/home/danny/privkey.pem'
	host = 'averi.cloud'
	port = 4430
	#secret_key = secrets.token_urlsafe(16)
	# Constant secret key for testing purposes
	secret_key = 'VEygPtzl8Kdf2HMKGuvkhA'
	user_id_session_key = 'userid'

# TODO: Put this in its own file and put it in .gitignore
class EmailConstants:
	'''
	This class contains constants used to send support emails

	Variables:
		from_address			The email address emails will be sent from
		from_password			The password of the from_address account
		smtp_server_address		The SMTP address of the email server 
			Use siatkosky.net, NOT smtp.siatkosky.net
			Use smtp.gmail.com, NOT gmail.com
			I am not sure why they are like this
		smtp_server_port		The SMTP port for the email server

	'''
	from_address = 'support@averi.cloud'
	from_password = 'not the real password because it shouldnt go on git lol'
	smtp_server_address = 'siatkosky.net'
	smtp_server_port = 465