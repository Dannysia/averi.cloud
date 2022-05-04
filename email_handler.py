import smtplib, _thread
from email.message import Message
from constants import EmailConstants


class EmailHandler:
    def __init__(self):
        self.cred_email = EmailConstants.from_address
        self.cred_password = EmailConstants.from_password

    # Functionality of sendMessage() - actually sends the email
    # Parameters: message: the message to send
    def sendMessage_util(self, sendto_email, subject, content):
        message = Message()
        message.add_header('from', EmailConstants.from_address)
        message.add_header('to', sendto_email)
        message.add_header('subject', subject)
        message.set_payload(content)
        message = message.as_string()
        server = smtplib.SMTP_SSL(EmailConstants.smtp_server_address, EmailConstants.smtp_server_port)
        server.login(self.cred_email, self.cred_password)
        server.sendmail(self.cred_email, sendto_email, message)
        server.quit()
    # Threaded helper function to send messages. This is threaded to prevent blocking
    # Parameters: message: the message to send
    def sendMessage(self, sendto_email, subject, content):
        _thread.start_new_thread(self.sendMessage_util, (sendto_email, subject, content,))
