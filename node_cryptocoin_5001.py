# =============================================================================
# Author : Sagar
# Description: Cryptocurrancy 
# Date : 08-27-2019
# =============================================================================

# Module 2 - Create a Cryptocurrancy

import datetime
import hashlib
import json                                                #to encode the block 
from flask import Flask,jsonify,request
import requests                                                 # for consenses
from uuid import uuid4
from urllib.parse import urlparse

#Part 1 - Building a blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block (proof = 1 , previous_hash = "0") 
        self.nodes = set()
    
    def create_block(self,proof,previous_hash): 
        block={'index': len(self.chain)+1,                     #Block Structure
               'timestamp': str(datetime.datetime.now()),
               'proof': proof,
               'previous_hash': previous_hash,
               'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block 
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if (hash_operation[:4] == '0000'):
                check_proof=True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self,block):
        encoded_block = json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self,chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest() #non symetrical
            if(hash_operation[:4] != '0000'):
                return False
            
            previous_block = block
            block_index += 1 
        return True
    
    def add_transaction(self,sender,receiver,amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self,address):               # address : address of the node
        parsed_url = urlparse(address)        # returns the ip,scheme,query,etc
        self.nodes.add(parsed_url.netloc)     # .netloc gives the ip 
        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if(response.status_code == 200):
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False
    
# Part 2 - Mining our Blockchain : Using Flask
        
# Creating a Web App
app = Flask(__name__)

# creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-','') 

# create blockchain
blockchain = Blockchain()

# Mining a new block
# http://127.0.0.1:5000/mine_block , Get Request
@app.route('/mine_block', methods = ['GET']) 
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address , receiver='Sagar' , amount =1)
    block = blockchain.create_block(proof,previous_hash)
    response = {'message' : 'Congratulations, you just mined a block!',
                'index' : block['index'],
                'timestamp' : block['timestamp'],
                'proof' : block['proof'],
                'previous_hash' : block['previous_hash'],
                'transactions' : block['transactions']}
    return jsonify(response),200

# Getting the full Blockchain
# http://127.0.0.1:5000/get_chain , Get Request
@app.route('/get_chain', methods = ['GET']) 

def get_chain():
    response = {'chain' : blockchain.chain,
                'length' : len(blockchain.chain)}
    return jsonify(response),200
 
#Checking chain is valid
#http://127.0.0.1:5000/validate_chain , Get Request
@app.route('/validate_chain', methods = ['GET'])
def validate_chain():
    valid = blockchain.is_chain_valid(blockchain.chain)
    if(valid==False):
        response = 'Chain is invalid'
    else:
        response = 'Chain is valid'
    
    return jsonify(response),200

# Adding a new transaction to the blockchain
@app.route('/add_transaction',methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','receiver','amount']
    if not all (key in json for key in transaction_keys):
        return 'Some element of transaction are missing' , 400
    index = blockchain.add_transaction(json['sender'],json['receiver'],json['amount'])
    response = {'message' : f'This transaction will be added to Block {index}'}
    return jsonify(response),201

# Part 3 - Decentalizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node",400
    for node in nodes:
        blockchain.add_node(node)
    
    response = {'message' : 'All the nodes are connected',
                'Total_node' : list(blockchain.nodes)}
    return jsonify(response),201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    if_chain_replaced = blockchain.replace_chain()
    if(if_chain_replaced==False):
        response = {'message': 'All Good ... chain is largest one',
                    'actual_chain': blockchain.chain}
    else:
        response = {'message': 'Chain replaced by largest one',
                    'new_chain': blockchain.chain}
    return jsonify(response),200

# Running the app
app.run(host='0.0.0.0',port=5001)




# =============================================================================
# Block:-
# Index ==> Block Number
# Timestamp ==> Time of Creation
# Proof ==> sha256 hash for function ((proof)^2 - (previous_proof)^2) should 
#           have four leading zeros.
# Previous_hash
#transaction ==> Detail of transaction
# =============================================================================

# For Geneces Block ==> Index = 1 and Previous_hash = 0
