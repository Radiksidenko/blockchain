import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
import pickle




class Blockchain:

    def __init__(self):
        self.current_transactions = [] #транзакции
        self.chain = []  #блоки
        self.nodes = set() #узлы

        # создаем родетельский блок
        self.new_block(previous_hash='0', proof=100)

    # регистрация узлов
    def register_node(self, address):
        parsed_url = urlparse(address)

        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc) #http://127.0.0.1:5000
        elif parsed_url.path:
            self.nodes.add(parsed_url.path) # 127.0.0.1:5000
        else:
            raise ValueError('Invalid URL')

#################################################################################

    def valid_chain(self, chain):
        # проверка блока на правильность построения

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # print("¢¢¢¢¢¢¢¢¢¢¢¢")
            # print(f'{last_block}')
            # print(f'{block}')
            # print("\n-----------\n")
            # print("¢¢¢¢¢¢¢¢¢¢¢¢")

            # проверка hash
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # проверка PoW
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

#################################################################################

    def resolve_conflicts(self):
        # консенсус просто заменяет без разбора самую длинную ветку

        neighbours = self.nodes
        new_chain = None


        max_length = len(self.chain)


        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            print(node)
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False

#################################################################################

    def new_block(self, proof, previous_hash):

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []

        self.chain.append(block)
        return block

#################################################################################

    def new_transaction(self, data):

        self.current_transactions.append({
            'data': data
        })
        return self.last_block['index'] + 1

#################################################################################

    @property
    def last_block(self):
        return self.chain[-1]

#################################################################################

    @staticmethod
    def hash(block):

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

#################################################################################

    def proof_of_work(self, last_block):


        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

#################################################################################

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

#################################################################################

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
# blockchain = Blockchain()


# test = Blockchain()
# print(test)
# fileObject = open(r"/Users/radomyrsidenko/Desktop/les/python/blockchain/Blockchain","w")
# fileObject.write(pickle.dump(test))
#
# # pickle.dump(test, fileObject)
# fileObject.close()


# example_dict = Blockchain()
#
# pickle_out = open("/Users/radomyrsidenko/Desktop/les/python/blockchain/Blockchain","wb")
# pickle.dump(example_dict, pickle_out)
# pickle_out.close()



pickle_in = open("/Users/radomyrsidenko/Desktop/les/python/blockchain/Blockchain","rb")
blockchain = pickle.load(pickle_in)

# print(example_dict)
#################################################################################

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)


    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    # for node in blockchain.nodes:
    #     print("mine:", node,"\n")
        # print(requests.get(f'http://{node}/nodes/resolve'))

    # requests.get('http://127.0.0.1:1337/test')

    pickle_out = open("/Users/radomyrsidenko/Desktop/les/python/blockchain/Blockchain", "wb")
    pickle.dump(blockchain, pickle_out)
    pickle_out.close()

    return jsonify(response), 200

#################################################################################

@app.route('/transactions/new', methods=['POST'])
def new_transaction():



    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ['data']

    for node in blockchain.nodes:
        print(node)
        requests.post(f'http://{node}/transactions_for_node', json=values)

    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['data'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201\

#################################################################################

@app.route('/transactions_for_node', methods=['POST'])
def node_transaction():

    values = request.get_json()
    required = ['data']

    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['data'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201\

#################################################################################

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
        'transactions': blockchain.current_transactions,
    }
    print("//////////////////")
    print("test",blockchain.nodes)
    print("//////////////////")
    return jsonify(response), 200

#################################################################################

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

#################################################################################

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    print("deg","|||||||||||||")
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

@app.route('/test', methods=['GET'])
def test():
    blockchain.resolve_conflicts()
    print("∑∑∑∑∑∑")

    return 'test', 201

#################################################################################

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)


#python start.py --port=1337

