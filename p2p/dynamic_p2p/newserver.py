import socket

host = '192.168.0.3'
port = 5001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(b'Hello, Node B!')
