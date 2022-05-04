Base python docs on: https://pandas.pydata.org/docs/development/contributing_docstring.html

flask_server.py must be run as a service user with passwordless sudo for wireguard_handler.py

This service user must also have write access to /etc/wireguard/wg0.conf

See if service user can have access to /etc/letsencrypt/live/averi.cloud/*, otherwise copy certificates to service user readable location

Ensure service user has read and write access to client config folder

Forward port 443 to internal flask port found in constants.py
	Example using internal port 4430
	sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 4430