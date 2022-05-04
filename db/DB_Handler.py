'''
This module contains functions and classes that interact with the database
Descriptions of parameters and variables are formatted as Table(Column) [Additional Information]

Classes:
	User
	Device
	DeviceFunction
	DB_Handler
'''

import mysql.connector, pyotp, hashlib, secrets, ipaddress
from constants import DatabaseConstants, WireguardConstants

class User:
	'''
	Represents a record from the Users table
	
	Member Variables:
		id 			Users(UserID)
		email		Users(Email)
		first_name	Users(FirstName)
		last_name	Users(LastName)
	'''
	def __init__(self, userid, email, first_name, last_name):
		self.id = userid
		self.email = email
		self.first_name = first_name
		self.last_name = last_name

class Device:
	'''
	Represents a record from the Devices and DeviceEndpoints tables

	Member Variables:
		id				Devices(DeviceID)
		ownerid			Devices(OwnerID)
		name			Devices(DeviceName)
		network_address	Devices(NetworkAddress)
		functions		Array of DeviceFunction objects
	'''
	def __init__(self, deviceid, ownerid, device_name, device_network_address, functions):
		self.id = deviceid
		self.ownerid = ownerid
		self.name = device_name
		self.network_address = device_network_address
		self.functions = functions

class DeviceFunction:
	'''
	Represents a record from the DeviceEndpoints table

	Member Variables:
		uri		DeviceEndpoints(EndpointURI)
		name	DeviceEndpoints(EndpointString)
		method	DeviceEndpoints(Method)
	'''
	def __init__(self, uri, name, method):
		self.uri = uri
		self.name = name
		self.method = method

class DB_Handler:
	'''
	Provides access to the database through parameterized functions

	Member Variables:
		db		Connection to the database
		cursor	Cursor connection to the database connection stored in db

	Functions:
		__init__
		add_user
		validate_login
		get_user_devices
		get_device_functions
		get_user_info
		validate_request
		get_largest_ip
		get_next_ip
		add_device
		get_id_from_token
		get_token_from_id
		get_config_file
		add_capability
		remove_token_config_access
	'''
	# Connect to the database
	def __init__(self):
		'''
		Initializes connection to the database

		Parameters:
			None
			[See DatabaseConstants for more information]

		Returns:
			Instance of DB_Handler
		'''
		self.db = mysql.connector.connect(
			host=DatabaseConstants.host,
			user=DatabaseConstants.user,
			password=DatabaseConstants.password
		)
		self.cursor = self.db.cursor()
		self.cursor.execute("use " + DatabaseConstants.database + ";")

	# Return is the seed for MFA
	def add_user(self, email, password, first_name, last_name):
		'''
		Adds a user to the database

		Parameters:
			email		Users(Email)
			password	Users(Password) [Unhashed]
			first_name	Users(FirstName)
			last_name	Users(LastName)

		Returns
			Success: mfa_seed	Users(MFASeed)
			Failure: False
		'''
		mfa_seed = pyotp.random_base32()
		salt = secrets.token_hex(4)
		# Define the query
		try:
			self.cursor.execute("INSERT INTO Users (Email, PasswordHash, Salt, MFASeed, FirstName, LastName) \
								VALUES (%(email)s, %(hashed_password)s, %(salt)s, %(mfa_seed)s, %(first_name)s, %(last_name)s);",
								# Parameterized inputs
								{
									'email' : email,
									'hashed_password' : hashlib.sha256((password + salt).encode()).hexdigest(),
									'salt' : salt,
									'mfa_seed' : mfa_seed,
									'first_name' : first_name,
									'last_name' : last_name
								})
			self.db.commit()
		except:
			return False
		return mfa_seed
	
	# All inputs should be strings
	# Returns UserID if valid login, -1 otherwise
	def validate_login(self, email, password, mfa_token):
		'''
		Checks credentials against database

		Parameters:
			email		Users(Email)
			password	Users(Password) [Unhashed]
			mfa_token	The MFA Token for Users(MFASeed) at the current time

		Returns:
			Valid Credentials: 	 userid
			Invalid Credentials: -1
		'''
		try:
			self.cursor.execute("SELECT UserID, PasswordHash, Salt, MFASeed FROM Users WHERE Email = %(email)s;", { 'email' : email })
			result = self.cursor.fetchall()[0]
		except:
			return -1
		user_id = result[0]
		password_hash = result[1]
		salt = result[2]
		mfa_seed = result[3]
		if hashlib.sha256((password + salt).encode()).hexdigest() != password_hash:
			return -1
		if pyotp.TOTP(mfa_seed).now() != mfa_token:
			return -1
		return user_id

	def get_user_devices(self, userid):
		'''
		Gets the devices owned by a user

		Parameters:
			userid	Users(UserID)

		Returns
			Array of Device objects
		'''
		device_list = []
		self.cursor.execute("SELECT DeviceID, DeviceName, INET6_NTOA(NetworkAddress) FROM Devices WHERE OwnerID = %(userID)s;", {'userID' : userid})
		for result in self.cursor.fetchall():
			device_list.append(Device(result[0], userid, result[1], result[2], self.get_device_functions(result[0])))
		return device_list

	# TODO: Combine with get_user_devices using joins
	def get_device_functions(self, deviceid):
		'''
		Gets the functions a device is capable of

		Parameters:
			deviceid	Devices(DeviceID)

		Returns:
			Array of DeviceFunction objects
		'''
		function_list = []
		self.cursor.execute("SELECT EndpointURI, EndpointString, Method FROM DeviceEndpoints WHERE DeviceID = %(deviceid)s;", {'deviceid' : deviceid})
		for result in self.cursor.fetchall():
			function_list.append(DeviceFunction(result[0], result[1], result[2]))
		return function_list

	def get_user_info(self, userid):
		'''
		Gets information about user

		Parameters:
			userid	Users(UserID)

		Returns:
			User object
			-1 in the event of invalid userid

		'''
		try:
			self.cursor.execute("SELECT Email, FirstName, LastName FROM Users WHERE UserID = %(userid)s", {'userid' : userid})
			result = self.cursor.fetchall()[0]
			return User(userid, result[0], result[1], result[2])
		except:
			return False
	
	def validate_request(self, userid, deviceid, uri, method):
		'''
		Validates that a request is valid

		Parameters:
			userid		Users(UserID)
			deviceid	Devices(DeviceID)
			uri			DeviceEndpoints(URI)
			method		DeviceEndpoints(Method)
		
		Returns:
			If Valid: Network address of device formatted as IPv6 string [Devices(NetworkAddress)]
			If invalid: False
		'''
		try:
			self.cursor.execute("SELECT INET6_NTOA(NetworkAddress) FROM Devices d \
								INNER JOIN DeviceEndpoints de on de.DeviceID = d.DeviceID \
								WHERE d.DeviceID = %(deviceid)s AND d.OwnerID = %(userid)s AND EndpointURI = %(uri)s AND Method = %(method)s;", 
								{'deviceid' : deviceid, 'userid' : userid, 'uri' : uri, 'method' : method})
			return self.cursor.fetchall()[0][0]
		except:
			return False
	
	def get_largest_ip(self):
		'''
		Get the largest IP address in Devices(NetworkAddresses)
		If no IPs are in the column, the value in WireguardConstants.initial_client_vpn_ip is returned

		Parameters:
			None

		Returns:
			Largest IP formatted as IPv6 string
		'''
		try:
			# this is needed, otherwise we will operate on cached data (the same ip is returned every time)
			self.db.commit()
			self.cursor.execute("SELECT INET6_NTOA(NetworkAddress) FROM Devices ORDER BY NetworkAddress desc LIMIT 1;")
			return self.cursor.fetchall()[0][0]
		except:
			return WireguardConstants.initial_client_vpn_ip
	
	def get_next_ip(self):
		'''
		Get the largest IP address that is 1 larger than the largest IP in Devices(NetworkAddresses)
		If no IPs are in the column, the value in WireguardConstants.initial_client_vpn_ip is returned

		Parameters:
			None

		Returns:
			Largest IP + 1 formatted as IPv6 string
		'''
		try:
			# this is needed, otherwise we will operate on cached data (the same ip is returned every time)
			self.db.commit()
			self.cursor.execute("SELECT INET6_NTOA(NetworkAddress) FROM Devices ORDER BY NetworkAddress desc LIMIT 1;")
			largest_ip = self.cursor.fetchall()[0][0]
			next_ip = str(ipaddress.ip_address(int(ipaddress.ip_address(largest_ip)) + 1))
			return next_ip
		except:
			return WireguardConstants.initial_client_vpn_ip

	# TODO use get_next_ip() instead of having network_address as a parameter
	# TODO generate random tokens here and return values
	def add_device(self, ownerid, name, network_address, config_file_name, token_one, token_two, token_three):
		'''
		Adds a device to Devices and a config access token to DeviceWireguardConfigs

		Parameters:
			ownerid				Users(UserID)
			name				Devices(Name)
			network_address		Devices(NetworkAddress)
			config_file_name	DeviceWireguardConfigs(ConfigFileName)
			token_one			DeviceWireguardConfigs(TokenOne)
			token_two			DeviceWireguardConfigs(TokenTwo)
			token_three			DeviceWireguardConfigs(TokenThree)
		
		Returns:
			True on success
			False on failure
		'''
		try:
			self.cursor.execute("INSERT INTO Devices (OwnerID, DeviceName, NetworkAddress) VALUES (%(OwnerID)s, %(DeviceName)s, INET6_ATON(%(NetworkAddress)s));",
								{'OwnerID' : ownerid, 'DeviceName' : name, 'NetworkAddress' : network_address})
			deviceID = self.cursor.lastrowid
			self.cursor.execute("INSERT INTO DeviceWireguardConfigs (DeviceID, ConfigFileName, TokenOne, TokenTwo, TokenThree) \
								VALUES (%(DeviceID)s, %(ConfigFileName)s, %(TokenOne)s, %(TokenTwo)s, %(TokenThree)s);",
								{"DeviceID" : deviceID, "ConfigFileName" : config_file_name, 'TokenOne' : token_one, 'TokenTwo' : token_two, 'TokenThree' : token_three})
			self.db.commit()
			return True
		except:
			return False

	def get_id_from_token(self, token):
		'''
		Get the ID associated with a token string

		Parameter:
			token	TokenList(Token)

		Returns:
			tokenid	TokenList(TokenID)
		'''
		try:
			self.cursor.execute("SELECT TokenID FROM TokenList WHERE Token = %(token)s;", {'token' : token})
			return self.cursor.fetchall()[0][0]
		except:
			return False

	def get_token_from_id(self, tokenid):
		'''
		Get the token string associated with a token ID

		Parameter:
			tokenid	TokenList(TokenID)

		Returns:
			token	TokenList(Token)
		'''
		try:
			self.cursor.execute("SELECT Token FROM TokenList WHERE TokenID = %(token)s;", {'token' : tokenid})
			return self.cursor.fetchall()[0][0]
		except:
			return False
	
	def get_config_file(self, tokenOne, tokenTwo, tokenThree):
		'''
		Get the device ID and path to the configuration file for a device

		Parameters:
			tokenOne	DeviceWireguardConfigs(TokenOne)
			tokenTwo	DeviceWireguardConfigs(TokenTwo)
			tokenThree	DeviceWireguardConfigs(TokenThree)

		Returns:
			Valid Tokens:
				Config File Name 	DeviceWireguardConfigs(ConfigFileName)
				DeviceID			Devices(DeviceID)
			Invalid Tokens: 
				False
				-1
		'''
		try:
			tokenOneVal = self.get_id_from_token(tokenOne)
			tokenTwoVal = self.get_id_from_token(tokenTwo)
			tokenThreeVal = self.get_id_from_token(tokenThree)
			self.cursor.execute("SELECT ConfigFileName, DeviceID FROM DeviceWireguardConfigs WHERE TokenOne = %(tokenOne)s AND TokenTwo = %(tokenTwo)s AND TokenThree = %(tokenThree)s;",
								{'tokenOne' : tokenOneVal, 'tokenTwo' : tokenTwoVal, 'tokenThree' : tokenThreeVal})
			result = self.cursor.fetchall()[0]
			return result[0], result[1]
		except:
			return False, -1

	def add_capability(self, deviceID, uri, string, method):
		'''
		Adds a capability to a device

		Parameters:
			deviceID	Devices(DeviceID)
			uri			DeviceEndpoints(EndpointURI)
			string		DeviceEndpoints(EndpointString)
			method		DeviceEndpoints(Method)

		Returns
			True on success
			False on failure
		'''
		try:
			self.cursor.execute("INSERT INTO DeviceEndpoints (DeviceID, EndpointURI, EndpointString, Method) VALUES (%(deviceid)s, %(uri)s, %(string)s, %(method)s);",
								{'deviceid' : int(deviceID), 'uri' : uri, 'string' : string, 'method' : method})
			self.db.commit()
			return True
		except:
			return False

	def remove_token_config_access(self, deviceid):
		'''
		Removes record from DeviceWireguardConfigs 

		Parameters:
			deviceID	Devices(DeviceID)
			
		Returns
			True on success
			False on failure
		'''
		try:
			self.cursor.execute("DELETE FROM DeviceWireguardConfigs WHERE DeviceID = %(deviceid)s", {'deviceid' : deviceid})
			self.db.commit()
			return True
		except:
			return False