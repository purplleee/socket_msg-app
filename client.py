import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=55555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def register_or_login(self):
        """Handle user registration or login"""
        while True:
            choice = input("1. Login\n2. Register\nChoice: ")
            username = input("Enter username: ")
            password = input("Enter password: ")
            
            if choice == "2":
                # Use "NEW|" to mark registration requests
                auth_string = f"NEW|{username}|{password}"
            else:
                auth_string = f"{username}|{password}"
            
            return auth_string
    
    def connect(self):
        """Modified connect method with authentication and debugging"""
        try:
            self.client.connect((self.host, self.port))
            
            # Get the auth string from register_or_login
            auth_string = self.register_or_login()  # This already returns the correctly formatted string
            
            # Debug: Print the auth string to verify the format
            print(f"DEBUG - Sending auth string: {auth_string}")
            
            self.client.send(auth_string.encode('utf-8'))
            
            # Receive authentication response
            response = self.client.recv(1024).decode('utf-8')
            print(f"DEBUG - Server response: {response}")
            
            if "Invalid" in response or "exists" in response:
                print(response)
                self.client.close()
                return False
            
            print(response)
            self.username = auth_string.split('|')[1] if 'NEW|' in auth_string else auth_string.split('|')[0]
            
            # Start message threads
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.send_messages()
            return True
            
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client.close()
            sys.exit(1)
   
    def receive_messages(self):
        """Receive and print messages from server"""
        while True:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message:
                    print(message)
                else:
                    print("Connection to server lost.")
                    self.client.close()
                    sys.exit(1)
            except:
                print("Connection to server lost.")
                self.client.close()
                sys.exit(1)
   
    def send_messages(self):
        """Send messages to server"""
        try:
            while True:
                message = input()
                if message.lower() == '/quit':
                    self.client.close()
                    sys.exit(0)
                self.client.send(message.encode('utf-8'))
        except:
            self.client.close()
            sys.exit(1)

if __name__ == "__main__":
    client = ChatClient()
    while not client.connect():
        choice = input("Try again? (y/n): ")
        if choice.lower() != 'y':
            sys.exit(1)