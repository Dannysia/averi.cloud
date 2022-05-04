flask_server.py must be run as a service user with passwordless sudo for wireguard_handler.py
	Example using user web-user
	sudo 'echo danny ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

This service user must also have write access to /etc/wireguard/wg0.conf
	In order to gain write access the following commands may be used
	sudo addgroup wgconfig
	sudo adduser danny wgconfig
	sudo usermod -a -G wgconfig danny
	sudo chgrp -R wgconfig /etc/wireguard
	sudo chmod -R g+rw /etc/wireguard
	sudo find /etc/wireguard -type d -exec chmod 2775 {} \;
	sudo find /etc/wireguard -type f -exec chmod ug+rw {} \;

See if service user can have access to /etc/letsencrypt/live/averi.cloud/*, otherwise copy certificates to service user readable location
	In order to gain write access the following commands may be used
	sudo addgroup ssl_access
	sudo adduser danny ssl_access
	sudo usermod -a -G ssl_access danny
	sudo chgrp -R ssl_access /etc/letsencrypt/live/averi.cloud/
	sudo chmod -R g+rw /etc/letsencrypt/live/averi.cloud/
	sudo find /etc/letsencrypt/live/averi.cloud/ -type d -exec chmod 2775 {} \;
	sudo find /etc/letsencrypt/live/averi.cloud/ -type f -exec chmod ug+rw {} \;
	Similar commands to above were used, but during testing this did not work

	See cert_instructions.txt for more information on certificate renewal

Ensure service user has read and write access to client config folder

Forward port 443 to internal flask port found in constants.py
	Example using internal port 4430
	sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 4430