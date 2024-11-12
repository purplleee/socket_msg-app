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
                username = f"NEW:{username}"
            
            return username, password
    
    def connect(self):
        """Modified connect method with authentication"""
        try:
            self.client.connect((self.host, self.port))
            
            # Handle authentication
            username, password = self.register_or_login()
            auth_string = f"{username}:{password}"
            self.client.send(auth_string.encode('utf-8'))
            
            # Receive authentication response
            response = self.client.recv(1024).decode('utf-8')
            if "Invalid" in response or "exists" in response:
                print(response)
                self.client.close()
                return False
            
            print(response)
            self.username = username.replace("NEW:", "")
            
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