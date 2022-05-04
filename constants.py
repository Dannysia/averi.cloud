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
	'''This class contains constants used by devices'''
	listen_port = 5000
	stream_port = 8080

class DatabaseConstants:
	'''This class contains constants used to connect to the database'''
	host = 'localhost'
	user = 'web_user'
	password = 'password'
	database = 'AVERI'

class WireguardConstants:
	'''This class contains constants used for WireGuard configuration'''
	client_config_dir = '/home/danny/client_configs/'
	# get this value from /etc/wireguard/wg0.conf on the server - run the privatekey through command echo privkey | wg pubkey where privkey is the private key
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
	'''This class contains constants used by the Flask server'''
	https_certificate_path = '/home/danny/cert.pem'
	https_keyfile_path = '/home/danny/privkey.pem'
	host = 'averi.cloud'
	port = 4430
	#secret_key = secrets.token_urlsafe(16)
	# Constant secret key for testing purposes
	secret_key = 'VEygPtzl8Kdf2HMKGuvkhA'
	user_id_session_key = 'userid'