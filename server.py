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

        # Load saved user credentials
        self.load_user_credentials()

    def broadcast(self, message, sender=None, target_channel=None):
        """Send message to all clients or only within a specific channel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        try:
            if target_channel:
                # Send message only to clients in the specified channel
                if target_channel in self.channels:
                    for client in self.channels[target_channel]['clients']:
                        if client != sender:
                            try:
                                client.send(formatted_message.encode('utf-8'))
                            except:
                                self.remove_client(client)
            else:
                # Broadcast to all connected clients
                for client in list(self.clients.keys()):
                    if client != sender:
                        try:
                            client.send(formatted_message.encode('utf-8'))
                        except:
                            self.remove_client(client)
        except Exception as e:
            print(f"Broadcast error: {e}")

    def load_user_credentials(self):
        """Load saved user credentials from file"""
        try:
            with open("user_info.txt", "r") as file:
                for line in file:
                    username, password = line.strip().split(':')
                    self.user_credentials[username] = password
        except FileNotFoundError:
            self.user_credentials = {'admin': 'admin123'}  # Default admin account

    def authenticate_user(self, username, password):
        """Check if username and password are valid"""
        return username in self.user_credentials and self.user_credentials[username] == password

    def register_user(self, username, password):
        """Register a new user and save to file"""
        if username in self.user_credentials:
            return False
        
        self.user_credentials[username] = password
        try:
            with open("user_info.txt", "a") as file:
                file.write(f"{username}:{password}\n")
            return True
        except Exception as e:
            print(f"Error saving user credentials: {e}")
            return False

    def handle_client(self, client_socket):
        """Handle client connection with proper error handling"""
        try:
            auth_data = client_socket.recv(1024).decode('utf-8').split('|')
            print(f"DEBUG - Received auth data: {auth_data}")

            if len(auth_data) == 3 and auth_data[0] == "NEW":
                # ... handle registration ...
                pass
            elif len(auth_data) == 2:
                username, password = auth_data
                if not self.authenticate_user(username, password):
                    client_socket.send("Invalid credentials.".encode('utf-8'))
                    return
                
                # Initialize client in the clients dictionary
                self.clients[client_socket] = (username, None, "online")
                client_socket.send("Welcome to the chat! Type /help for commands.".encode('utf-8'))
                self.broadcast(f"{username} joined the chat!", sender=client_socket)
                
                # Handle messages from client
                while True:
                    try:
                        message = client_socket.recv(1024).decode('utf-8')
                        if not message:
                            break
                        
                        if message.startswith('/'):
                            self.process_command(client_socket, message)
                        else:
                            username, current_channel, _ = self.clients[client_socket]
                            if current_channel:
                                # Send to specific channel
                                formatted_msg = f"{username}: {message}"
                                self.broadcast(formatted_msg, sender=client_socket, target_channel=current_channel)
                            else:
                                # Broadcast to all users
                                formatted_msg = f"{username}: {message}"
                                self.broadcast(formatted_msg, sender=client_socket)
                                
                    except Exception as e:
                        print(f"Error handling message: {e}")
                        break
                        
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """Remove client and clean up with proper tuple unpacking"""
        if client_socket in self.clients:
            try:
                username, current_channel, status = self.clients[client_socket]
                if current_channel:
                    self.leave_channel(client_socket)
                self.broadcast(f"{username} has disconnected.")
                del self.clients[client_socket]
            except Exception as e:
                print(f"Error removing client: {e}")
            finally:
                try:
                    client_socket.close()
                except:
                    pass

    def process_command(self, client_socket, command):
        """Process client commands"""
        try:
            username, current_channel, status = self.clients[client_socket]
            tokens = command.split()
            cmd = tokens[0].lower()

            if cmd.startswith('/'): # It's a command
                if cmd == '/help':
                    help_text = """Available commands:
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
                    
                elif cmd == '/create':
                    if len(tokens) < 3:
                        client_socket.send("Usage: /create <channel> <password>".encode('utf-8'))
                    else:
                        channel_name, password = tokens[1], tokens[2]
                        if channel_name in self.channels:
                            client_socket.send("Channel already exists.".encode('utf-8'))
                        else:
                            self.channels[channel_name] = {'clients': [], 'password': password}
                            client_socket.send(f"Private channel {channel_name} created.".encode('utf-8'))
                            
                elif cmd == '/join':
                    if len(tokens) < 2:
                        client_socket.send("Usage: /join <channel> [password]".encode('utf-8'))
                    else:
                        channel_name = tokens[1]
                        password = tokens[2] if len(tokens) > 2 else None
                        self.join_channel(client_socket, channel_name, password)
                        
                elif cmd == '/leave':
                    if current_channel:
                        self.leave_channel(client_socket)
                    else:
                        client_socket.send("You are not in any channel.".encode('utf-8'))
                        
                elif cmd == '/list':
                    channels = list(self.channels.keys())
                    response = "Available channels: " + (", ".join(channels) if channels else "No channels available")
                    client_socket.send(response.encode('utf-8'))
                    
                elif cmd == '/quit':
                    raise Exception("Client quit")
                    
                else:
                    client_socket.send("Unknown command. Type /help for available commands.".encode('utf-8'))
            else:
                # It's a regular message
                if current_channel:
                    formatted_msg = f"{username}: {command}"
                    self.broadcast(formatted_msg, sender=client_socket, target_channel=current_channel)
                else:
                    client_socket.send("Join a channel first using /join <channel>".encode('utf-8'))
                    
        except Exception as e:
            print(f"Error processing command: {e}")
            self.remove_client(client_socket)

    def join_channel(self, client_socket, channel_name, password=None):
        """Join a client to a channel, checking for private access if needed"""
        try:
            if client_socket in self.clients:
                username, current_channel, status = self.clients[client_socket]
                
                # Leave current channel if in one
                if current_channel:
                    self.leave_channel(client_socket)

            # Create channel if it doesn't exist
            if channel_name not in self.channels:
                self.channels[channel_name] = {
                    'clients': [],
                    'password': password
                }

            # Check password if channel is private
            if self.channels[channel_name].get('password') and self.channels[channel_name]['password'] != password:
                client_socket.send("Incorrect password for private channel.".encode('utf-8'))
                return

            # Add client to channel
            if client_socket not in self.channels[channel_name]['clients']:
                self.channels[channel_name]['clients'].append(client_socket)
                username = self.clients[client_socket][0]
                self.clients[client_socket] = (username, channel_name, self.clients[client_socket][2])
                
                # Notify channel about new user
                join_message = f"{username} joined {channel_name}"
                self.broadcast(join_message, sender=client_socket, target_channel=channel_name)
                client_socket.send(f"Joined channel {channel_name}".encode('utf-8'))
                
        except Exception as e:
            print(f"Error joining channel: {e}")
            client_socket.send("Error joining channel.".encode('utf-8'))

    def leave_channel(self, client_socket):
        """Remove client from their current channel"""
        if client_socket in self.clients:
            username, current_channel, status = self.clients[client_socket]
            if current_channel and current_channel in self.channels:
                if client_socket in self.channels[current_channel]['clients']:
                    self.channels[current_channel]['clients'].remove(client_socket)
                    if not self.channels[current_channel]['clients']:  # Remove empty channel
                        del self.channels[current_channel]
                    self.clients[client_socket] = (username, None, status)
                    self.broadcast(f"{username} left {current_channel}.", target_channel=current_channel)
                    client_socket.send(f"Left channel {current_channel}".encode('utf-8'))

    def start(self):
        """Start the server"""
        print("Server is ready to accept connections...")
        while not self.shutdown_flag:
            try:
                client_socket, address = self.server.accept()
                print(f"New connection from {address}")
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error accepting connection: {e}")
                if not self.shutdown_flag:
                    continue

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown_flag = True