''' 
This module contains classes and functions related to Wireguard configuration and management

Classes: 
	WireguardConfig

'''

from db import DB_Handler
from constants import WireguardConstants

class WireguardConfig:
	'''
	This class contains functions related to Wireguard configuration and management

	Member Variables:
		db	Instance of DB_Handler

	Functions:
		__init__
		add_client
	'''
	def __init__(self):
		'''
		Instantiates the class

		Parameters:
			None

		Returns:
			Instance of WireguardConfig
		'''
		self.db = DB_Handler.DB_Handler()
	
	def add_client(self):
		'''
		Adds a client to Wireguard and generates a config file for it

		Parameters:
			None
			[See WireguardConstants for more information]

		Returns:
			Success:
				IPv6 string address of the configuration
			Failure:
				False

		'''
		import subprocess
		import ipaddress
		
		try:
			# This must be defined outside the dictionary definition since it is used twice and results in a random variable
			client_private_key = str(subprocess.check_output('wg genkey', shell=True))[2:-3]
			
			client_dict = {
				# 30 seconds between keepalive packets
				'keepalive_time' : WireguardConstants.keepalive_time,
				'client_private_key' : client_private_key,
				'client_public_key' : str(subprocess.check_output('echo {} | wg pubkey'.format(client_private_key), shell=True))[2:-3],
				'client_preshared_key' : str(subprocess.check_output('wg genpsk', shell=True))[2:-3],
				# The IPs of the client and server within the VPN
				#'client_address' : str(ipaddress.ip_address(int(ipaddress.ip_address(self.db.get_largest_ip())) + 1)),
				'client_address' : str(ipaddress.ip_address(self.db.get_next_ip())),
				'server_address' : str(ipaddress.ip_address(WireguardConstants.server_vpn_ip)),
				# The Domain of the server
				'server_public_domain' : WireguardConstants.server_domain,
				'server_public_key' : WireguardConstants.server_public_key,
				'server_port' : WireguardConstants.server_port
			}

			client_config_text = WireguardConstants.client_config_string.format(**client_dict)
			server_config_text = WireguardConstants.server_config_string.format(**client_dict)

			# write client config
			client_config = open(WireguardConstants.client_config_dir + str(client_dict['client_address']).replace(':', ''), 'w')
			client_config.write(client_config_text)
			client_config.close()

			# write server config
			############### Permissions errors? #########################
			# sudo addgroup wgconfig                                    #
			# sudo adduser danny wgconfig                               #
			# sudo usermod -a -G wgconfig danny                         #
			# sudo chgrp -R wgconfig /etc/wireguard                     #
			# sudo chmod -R g+rw /etc/wireguard                         #
			# sudo find /etc/wireguard -type d -exec chmod 2775 {} \;   #
			# sudo find /etc/wireguard -type f -exec chmod ug+rw {} \;  #
			#############################################################
			server_config = open(WireguardConstants.server_config_path, 'a')
			server_config.write(server_config_text)
			server_config.close()

			# needs to run as root. regular cronjob? maybe. or use service account that doesn't need password for sudo
			#subprocess.check_output("sudo wg syncconf " + WireguardConstants.server_interface + " <(wg-quick strip " + WireguardConstants.server_interface + ")", shell=True)
			# these also need to run as root
			#subprocess.check_output("sudo wg-quick down " + WireguardConstants.server_interface, shell=True)
			#subprocess.check_output("sudo wg-quick up " + WireguardConstants.server_interface, shell=True)

			return client_dict['client_address']
		except:
			return False