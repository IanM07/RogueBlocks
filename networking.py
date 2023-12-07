import socket
import json
import threading
import pygame
import datetime
from cfg import (screen_width, screen_height, BAR_WIDTH, BAR_HEIGHT, BAR_X, BAR_Y,
                    WHITE, BLACK, RED, GREEN, BLUE, initial_player_x, initial_player_y,
                    number_of_enemies, is_multiplayer, network_socket, is_host, screen)

def log_message(message):
    """Helper function to log a message with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - {message}")
    
# Networking setup
def setup_server(host, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        log_message(f"Server started, listening on {host}:{port}")
        client_socket, addr = server_socket.accept()
        log_message(f"Client connected from {addr}")
        return client_socket
    except socket.error as e:
        log_message(f"Server setup failed: {e}")
        return None

def setup_client(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        log_message(f"Connected to server at {host}:{port}")
        return client_socket
    except socket.error as e:
        log_message(f"Client setup failed: {e}")
        return None


def serialize_game_state(player, enemies, projectiles):
    try:
        game_state = {
            'player': {'x': player.x, 'y': player.y, 'hp': player.hp},
            'projectiles': [{'id': p.id, 'x': p.x, 'y': p.y} for p in projectiles] if projectiles else [],
            'enemies': [{'x': e.x, 'y': e.y} for e in enemies] if enemies else [],
            'enemy_count': len(enemies) if enemies else 0
        }
        return json.dumps(game_state)
    except Exception as e:
        print(f"Error serializing game state: {e}")
        return None

# New function to send the complete game state from host to remote
def send_host_state_to_remote(sock, player, enemies, projectiles):
    try:
        game_state = {
            'player': {'x': player.x, 'y': player.y, 'hp': player.hp},
            'enemies': [{'x': e.x, 'y': e.y} for e in enemies],
            'projectiles': [{'id': p.id, 'x': p.x, 'y': p.y} for p in projectiles]
        }
        serialized_data = json.dumps(game_state).encode('utf-8')  # Ensure serialization is done before sending
        sock.sendall(serialized_data)
        log_message(f"Sent data to remote: {serialized_data}")
    except Exception as e:
        log_message(f"Error sending host state to remote: {e}")

# New function to send only the remote player's data to the host
def send_remote_state_to_host(sock, player, projectiles):
    remote_state = {
        'player': {'x': player.x, 'y': player.y},
        'projectiles': [{'x': p.x, 'y': p.y, 'id': p.id} for p in projectiles]
    }
    try:
        serialized_data = json.dumps(remote_state).encode('utf-8')
        sock.sendall(serialized_data)
    except Exception as e:
        print(f"Error sending remote state to host: {e}")

def deserialize_game_state(data):
    try:
        return json.loads(data.decode('utf-8'))
    except Exception as e:
        print(f"Error deserializing game state: {e}")
        return None

def receive_game_state(sock):
    try:
        sock.setblocking(0)
        data = sock.recv(4096)
        if data:
            return deserialize_game_state(data)
        return None
    except BlockingIOError:
        return None
    except socket.error as e:
        print(f"Error receiving game state: {e}")
        return None
