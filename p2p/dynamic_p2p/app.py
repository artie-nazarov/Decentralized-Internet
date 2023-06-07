from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from node import Node
from sovrin_utils import create_wallet, create_did, create_pairwise, authenticate_user

# Create an instance of Flask
app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create an instance of SQLAlchemy
db = SQLAlchemy(app)

# Import the User model
from models import User

# Create an instance of the Node class
node = Node()

# Initialize the database
db.create_all()

# Register routes for node operations
@app.route('/register/node', methods=['POST'])
def register_node():
    next_node_uri = request.json.get('next_node_uri')
    node.set_next_node(next_node_uri)
    return jsonify({'message': 'Node registered successfully'})

@app.route('/send-message', methods=['POST'])
def send_message():
    message = request.json.get('message')
    node.send_message(message)
    return jsonify({'message': 'Message sent'})

# Register routes for user operations
@app.route('/register/user', methods=['POST'])
def register_user():
    username = request.json.get('username')
    password = request.json.get('password')
    email = request.json.get('email')
    user = User(username=username, password=password, email=email)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})

@app.route('/authenticate', methods=['POST'])
def authenticate():
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'message': 'User not found'})
    if user.password != password:
        return jsonify({'message': 'Invalid password'})
    return jsonify({'message': 'Authentication successful'})

# Register routes for Sovrin operations
@app.route('/create-wallet', methods=['POST'])
def create_wallet_route():
    wallet_name = request.json.get('wallet_name')
    wallet_pass = request.json.get('wallet_pass')
    wallet_handle = create_wallet(wallet_name, wallet_pass)
    return jsonify({'message': 'Wallet created successfully', 'wallet_handle': wallet_handle})

@app.route('/create-did', methods=['POST'])
def create_did_route():
    wallet_handle = request.json.get('wallet_handle')
    did = create_did(wallet_handle)
    return jsonify({'message': 'DID created successfully', 'did': did})

@app.route('/create-pairwise', methods=['POST'])
def create_pairwise_route():
    wallet_handle = request.json.get('wallet_handle')
    my_did = request.json.get('my_did')
    their_did = request.json.get('their_did')
    their_ver_key = request.json.get('their_ver_key')
    create_pairwise(wallet_handle, my_did, their_did, their_ver_key)
    return jsonify({'message': 'Pairwise connection created successfully'})

@app.route('/authenticate-user', methods=['POST'])
def authenticate_user_route():
    wallet_name = request.json.get('wallet_name')
    wallet_pass = request.json.get('wallet_pass')
    their_did = request.json.get('their_did')
    authenticated = authenticate_user(wallet_name, wallet_pass, their_did)
    return jsonify({'authenticated': authenticated})

if __name__ == '__main__':
    app.run(port=5001)
