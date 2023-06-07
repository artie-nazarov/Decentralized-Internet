import Pyro4
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from models import User
from sovrin_utils import *
import asyncio
from functools import wraps


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    db.create_all()

nodes = {}  # Dictionary to store the node information
def initialize_database():
    with app.app_context():
        db.create_all()

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

nodes = {}  # Dictionary to store the node information

class Node:
    def __init__(self, node_id):
        self.node_id = node_id
        self.next_node_uri = None

    def set_next_node(self, next_node_uri):
        self.next_node_uri = next_node_uri

    def send_message(self, message):
        if self.next_node_uri:
            print(f"Node {self.node_id} is sending '{message}' to the next node")
            next_node = Pyro4.Proxy(self.next_node_uri)
            next_node.send_message(message)
            print(f"Node {self.node_id} sent the message '{message}'")
        else:
            print(f"Node {self.node_id} received the message '{message}'")

@app.route('/register', methods=['POST'])
def register_node():
    node_id = request.json['node_id']
    node = Node(node_id)
    nodes[node_id] = node
    return f"Node {node_id} registered successfully."

@app.route('/register/user', methods=['POST'])  # New endpoint for user registration
def register_user():
    # Retrieve the username, password, and email from the request's JSON data
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']

    try:
        # Create a new user object and save it to the database
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()

        return f"User {username} registered successfully."
    except Exception as e:
        db.session.rollback()
        return f"An error occurred: {str(e)}"

@app.route('/connect', methods=['POST'])
def connect_nodes():
    sender_id = request.json['sender_id']
    receiver_id = request.json['receiver_id']
    sender_node = nodes.get(sender_id)
    receiver_node = nodes.get(receiver_id)

    if sender_node and receiver_node:
        sender_node.set_next_node(receiver_node.node_id)
        return f"Node {sender_id} connected to Node {receiver_id}."
    else:
        return "Invalid node IDs."

@app.route('/send', methods=['POST'])
def send_message():
    sender_id = request.json['sender_id']
    message = request.json['message']
    sender_node = nodes.get(sender_id)

    if sender_node:
        sender_node.send_message(message)
        return f"Node {sender_id} sent the message '{message}'."
    else:
        return "Invalid node ID."

#def async_wrapper(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

    return wrapped

@app.route('/authenticate', methods=['POST'])
def authenticate_user_route():
    wallet_name = request.json['wallet_name']
    wallet_pass = request.json['wallet_pass']
    their_did = request.json['their_did']

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    authenticated = loop.run_until_complete(authenticate_user(wallet_name, wallet_pass, their_did))

    if authenticated:
        return "User authenticated successfully."
    else:
        return "Authentication failed."
if __name__ == '__main__':
    app.run(port=5001)
