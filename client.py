import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=55555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
    
    def register_or_login(self):
        """Handle user registration or login"""
        while True:
            choice = input("1. Login\n2. Register\nChoice: ")
            if choice not in ['1', '2']:
                print("Invalid choice. Please enter 1 or 2.")
                continue
            
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            
            if not username or not password:
                print("Username and password cannot be empty.")
                continue
            
            if choice == "2":
                auth_string = f"NEW|{username}|{password}"
            else:
                auth_string = f"{username}|{password}"
            
            return auth_string
    
    def connect(self):
        """Connect to server with improved error handling"""
        try:
            self.client.connect((self.host, self.port))
            auth_string = self.register_or_login()
            print(f"DEBUG - Sending auth string: {auth_string}")
            
            self.client.send(auth_string.encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')
            print(f"DEBUG - Server response: {response}")
            
            if "Invalid" in response or "exists" in response:
                print(response)
                self.client.close()
                return False
            
            print(response)
            self.username = auth_string.split('|')[1] if 'NEW|' in auth_string else auth_string.split('|')[0]
            
            if 'NEW|' in auth_string:
                print("Please log in with your new credentials.")
                return False
            
            # Start message threads
            receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            receive_thread.start()
            self.send_messages()
            return True
            
        except ConnectionRefusedError:
            print("Could not connect to server. Please check if the server is running.")
            return False
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
        finally:
            if not self.running:
                self.client.close()
    
    def receive_messages(self):
        """Receive messages from server"""
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message:
                    print("\nDisconnected from server.")
                    self.running = False
                    break
                print(message)
            except Exception as e:
                if self.running:
                    print("\nLost connection to server.")
                    self.running = False
                break
    
    def send_messages(self):
        """Send messages to server"""
        try:
            while self.running:
                message = input()
                if message.lower() == '/quit':
                    self.running = False
                    self.client.send(message.encode('utf-8'))
                    break
                elif message:
                    self.client.send(message.encode('utf-8'))
        except Exception as e:
            if self.running:
                print(f"Error sending message: {e}")
        finally:
            self.running = False
            self.client.close()

if __name__ == "__main__":
    client = ChatClient()
    while True:
        if not client.connect():
            choice = input("Try again? (y/n): ")
            if choice.lower() != 'y':
                break
        else:
            break
    sys.exit(0)