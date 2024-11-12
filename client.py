import socket
import threading
import sys

class ChatClient:
    def __init__(self, host='127.0.0.1', port=55555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   
    def connect(self, username):
        """Connect to the server"""
        try:
            self.client.connect((self.host, self.port))
            self.username = username
            self.client.send(username.encode('utf-8'))
           
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.send_messages()
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
    username = input("Enter your username: ")
    client = ChatClient()
    client.connect(username)