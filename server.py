import socket
import threading
from datetime import datetime

class ChatServer:
    def __init__(self, host='127.0.0.1', port=55555):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.server.settimeout(1)
       
        self.clients = {}  # {client_socket: (username, current_channel, status)}
        self.channels = {}  # {channel_name: [client_sockets]}
        self.user_credentials = {}  # {username: password}
        self.shutdown_flag = False
        print(f"Server running on {host}:{port}")

        # Load saved user credentials (you can replace this with a database later)
        self.load_user_credentials()

    def broadcast(self, message, sender=None, target_channel=None):
        """Send message to all clients or only within a specific channel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] {message}"
       
        if target_channel:
            clients = self.channels.get(target_channel, [])
        else:
            clients = self.clients.keys()
       
        for client in clients:
            if client != sender:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    self.remove_client(client)


    def load_user_credentials(self):
        """Load saved user credentials (simplified version using a dictionary)"""
        # In a real application, you'd load this from a database or file
        self.user_credentials = {
            'admin': 'admin123',  # Just for testing
        }

    def authenticate_user(self, username, password):
        """Check if username and password are valid"""
        return username in self.user_credentials and self.user_credentials[username] == password

    def register_user(self, username, password):
        """Register a new user and save to a .txt file"""
        if username in self.user_credentials:
            return False
        self.user_credentials[username] = password
        
        # Save to user_info.txt
        with open("user_info.txt", "a") as file:
            file.write(f"{username}:{password}\n")
        
        return True


    def handle_client(self, client_socket):
        """Modified handle_client method with authentication and debugging"""
        try:
            # Receive authentication data
            auth_data = client_socket.recv(1024).decode('utf-8').split(':')
            
            # Debug: Print the received data
            print(f"DEBUG - Received auth data: {auth_data}")
            
            if len(auth_data) != 2:
                client_socket.send("Invalid authentication format.".encode('utf-8'))
                return
            
            username, password = auth_data
            
            # Check if it's a registration request
            if username.startswith("NEW:"):
                username = username[4:]  # Remove "NEW:" prefix
                if self.register_user(username, password):
                    client_socket.send("Registration successful!".encode('utf-8'))
                else:
                    client_socket.send("Username already exists.".encode('utf-8'))
                    return
            
            # Authenticate existing user
            elif not self.authenticate_user(username, password):
                client_socket.send("Invalid credentials.".encode('utf-8'))
                return
            
            # If authentication successful, proceed with chat
            self.clients[client_socket] = (username, None, "online")
            self.broadcast(f"{username} joined the chat!", sender=client_socket)
            client_socket.send("Welcome to the chat! Type /help for commands.".encode('utf-8'))

            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    if message.startswith('/'):
                        self.process_command(client_socket, message)
                    else:
                        username, channel, status = self.clients[client_socket]
                        if channel:
                            self.broadcast(f"{username}: {message}", sender=client_socket, target_channel=channel)
                        else:
                            self.broadcast(f"{username}: {message}", sender=client_socket)
                else:
                    break
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client(client_socket)


    def process_command(self, client_socket, command):
        """Enhanced process_command method with user management commands"""
        username, current_channel, status = self.clients[client_socket]
        tokens = command.split()
        cmd = tokens[0].lower()
        
        if cmd == '/help':
            help_text = """Commands:
                                    /help - Show this help message
                                    /list - List available channels
                                    /join <channel> - Join a channel
                                    /leave - Leave current channel
                                    /users - List all online users
                                    /nick <new_name> - Change your nickname
                                    /status <away/online> - Change your status
                                    /msg <user> <message> - Send private message
                                    /quit - Disconnect from server"""
            client_socket.send(help_text.encode('utf-8'))
            
        elif cmd == '/users':
            users_list = []
            for sock, (name, chan, stat) in self.clients.items():
                users_list.append(f"{name} ({stat})")
            client_socket.send(f"Online users: {', '.join(users_list)}".encode('utf-8'))
            
        elif cmd == '/nick':
            if len(tokens) < 2:
                client_socket.send("Usage: /nick <new_nickname>".encode('utf-8'))
                return
            new_nick = tokens[1]
            if new_nick in [name for _, (name, _, _) in self.clients.items()]:
                client_socket.send("Nickname already taken.".encode('utf-8'))
                return
            old_nick = username
            self.clients[client_socket] = (new_nick, current_channel, status)
            self.broadcast(f"{old_nick} is now known as {new_nick}")
            
        elif cmd == '/status':
            if len(tokens) < 2 or tokens[1] not in ['away', 'online']:
                client_socket.send("Usage: /status <away/online>".encode('utf-8'))
                return
            new_status = tokens[1]
            self.clients[client_socket] = (username, current_channel, new_status)
            self.broadcast(f"{username} is now {new_status}")
        elif cmd == '/list':
            channels = "Available channels: " + ", ".join(self.channels.keys())
            client_socket.send(channels.encode('utf-8'))
        elif cmd == '/join':
            if len(tokens) < 2:
                client_socket.send("Usage: /join <channel>".encode('utf-8'))
            else:
                channel = tokens[1]
                if current_channel:
                    self.leave_channel(client_socket)
                self.join_channel(client_socket, channel)
        elif cmd == '/leave':
            self.leave_channel(client_socket)
        elif cmd == '/quit':
            self.remove_client(client_socket)
        else:
            client_socket.send("Unknown command. Type /help for a list of commands.".encode('utf-8'))

    def join_channel(self, client_socket, channel_name):
        """Join a client to a channel"""
        if channel_name not in self.channels:
            self.channels[channel_name] = []
        self.channels[channel_name].append(client_socket)
        self.clients[client_socket] = (self.clients[client_socket][0], channel_name)
        self.broadcast(f"{self.clients[client_socket][0]} joined {channel_name}.", target_channel=channel_name)

    def leave_channel(self, client_socket):
        """Remove client from their current channel"""
        username, current_channel = self.clients[client_socket]
        if current_channel and client_socket in self.channels[current_channel]:
            self.channels[current_channel].remove(client_socket)
            self.broadcast(f"{username} left {current_channel}.", target_channel=current_channel)
            self.clients[client_socket] = (username, None)

    def remove_client(self, client_socket):
        """Remove client and clean up"""
        if client_socket in self.clients:
            username, current_channel = self.clients[client_socket]
            if current_channel:
                self.leave_channel(client_socket)
            del self.clients[client_socket]
            client_socket.close()
            self.broadcast(f"{username} has disconnected.")

    def start(self):
        """Start the server and accept connections"""
        while not self.shutdown_flag:
            try:
                client_socket, _ = self.server.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except socket.timeout:
                continue

if __name__ == "__main__":
    server = ChatServer()
    server.start()