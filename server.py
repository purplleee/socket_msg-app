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
       
        self.clients = {}  # {client_socket: (username, current_channel)}
        self.channels = {}  # {channel_name: [client_sockets]}
        self.shutdown_flag = False
        print(f"Server running on {host}:{port}")

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

    def handle_client(self, client_socket):
        """Handle individual client connection"""
        try:
            username = client_socket.recv(1024).decode('utf-8')
            self.clients[client_socket] = (username, None)
            self.broadcast(f"{username} joined the chat!", sender=client_socket)
            client_socket.send("Welcome to the chat! Type /help for commands.".encode('utf-8'))

            while True:
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    if message.startswith('/'):
                        self.process_command(client_socket, message)
                    else:
                        username, channel = self.clients[client_socket]
                        if channel:
                            self.broadcast(f"{username}: {message}", sender=client_socket, target_channel=channel)
                        else:
                            self.broadcast(f"{username}: {message}", sender=client_socket)
                else:
                    break
        except:
            pass
        finally:
            self.remove_client(client_socket)

    def process_command(self, client_socket, command):
        """Process commands from clients"""
        username, current_channel = self.clients[client_socket]
        tokens = command.split()
        cmd = tokens[0].lower()
       
        if cmd == '/help':
            client_socket.send("Commands:\n/help\n/list\n/join <channel>\n/leave\n/quit\n".encode('utf-8'))
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