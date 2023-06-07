import Pyro4
import time
import uuid
import sys

class Node:
    def __init__(self):
        # generate a unique identifier for the node
        self.node_id = str(uuid.uuid4())
        print(f"Node ID: {self.node_id}")
        # this line identifies that there is no next node connected initially
        self.next_node_uri = None
        # locate the Pyro4 name server
        self.ns = Pyro4.locateNS()

    # this is a method of the node class that allows setting the URI of the next node 
    def set_next_node(self, next_node_uri):
        # this line assigns the provided 'next_node_uri' to the 'next_node_uri' attribute of the current node object
        self.next_node_uri = next_node_uri

    # this is a method to retrieve the node ID
    def get_node_id(self):
        return self.node_id
    # this method allows a current node to send a message to the next connected node
    def send_message(self, message):
        # checking there is a next node URI specified 
        if self.next_node_uri:
            # current node sending message to next node
            print(f"{self.node_id} is sending '{message}' to next node")
            # Creating a proxy object 'next node' with the Pyro4 library to represent the remote object located at the URI specified by the next_node_uri
            next_node = Pyro4.Proxy(self.next_node_uri)
            # using send_message method on the next_node object passing the message as an argument 
            next_node.send_message(message)
            # indicating that the message has been sent 
            print(f"{self.node_id} sent the message '{message}'")
        # executed when there is no next node URI specified
        else:
            # prints a message indicating that the other node has received a message 
            print(f"{self.node_id} received the message '{message}'")

    # method to register the node with the server
    def register_node(self):
    # register the node URI with the server using the node ID as the key
        self.ns.register(str(self.node_id), str(node_uri))
        print(f"Registered node with ID: {self.node_id} and URI: {str(node_uri)}")
    # method to unregister the node from the server
    def unregister_node(self):
        self.ns.remove(str(self.node_id))
        
        
        
if __name__ == '__main__':
# Check if a port number is provided as a command-line argument
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1024 or port > 65535:
                raise ValueError
        except ValueError:
            print("Invalid port number. Please provide a valid port number between 1024 and 65535.")
            sys.exit(1)
    else:
        # Default port if no command-line argument is provided
        port = 5001     
        
# create an instance of the Node class named node
node = Node()

# create a Pyro4 daemon which will be used to register and handle remote objects 
daemon = Pyro4.Daemon(port=port)

# register the node object with the Pyro4 Daemon, returning a URI that can be used to access the object remotely 
node_uri = daemon.register(node)

# register the node URI with the Pyro4 name server using the node ID as the key
node.register_node()

# Wait for other nodes to join the network
print("Waiting for other nodes to join the network...")
while True:
    try:
        # get a list of all the registered nodes
        nodes = node.ns.list()
        # exclude the current node from the list
        nodes.pop(str(node.node_id), None)
        # if there are other nodes in the network, break out of the loop
        if nodes:
            break
        # if there are no other nodes in the network, wait for 1 second before checking again
        time.sleep(1)
    except Pyro4.errors.NamingError:
        print("pyro naming error")
        pass

# get the URI of the first node in the list of registered nodes
next_node_uri = node.ns.lookup(list(nodes.keys())[0])
node.set_next_node(next_node_uri)