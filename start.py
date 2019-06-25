# -*- coding: utf-8 -*-
import hashlib
import json
from time import time
from urlparse import urlparse
from uuid import uuid4
import requests
from flask import Flask, jsonify, request
import pickle


class Blockchain:

    def __init__(self):
        self.current_transactions = []  # транзакции
        self.chain = []  # блоки
        self.nodes = set()  # узлы

        # создаем родетельский блок
        self.new_block(previous_hash='0')

    # регистрация узлов
    def register_node(self, address):
        parsed_url = urlparse(address)

        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)  # http://127.0.0.1:5000
        elif parsed_url.path:
            self.nodes.add(parsed_url.path)  # 127.0.0.1:5000
            raise ValueError('Invalid URL')

    #################################################################################

    def valid_chain(self, chain):
        # проверка блока на правильность построения

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # проверка hash
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            last_block = block
            current_index += 1

        return True

    #################################################################################

    def resolve_conflicts(self):
        # получить цепочку просто заменяет без разбора самую длинную ветку

        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get('http://{node}/chain')
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

    def new_block(self, previous_hash):

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'validator': "validator",
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


app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
routToFile = "/Users/radomyrsidenko/Desktop/универ/Диплом/git/test/Blockchain"
blockchain = Blockchain()

# pickle_out = open("/Users/radomyrsidenko/Desktop/универ/Диплом/git/test/Blockchain","wb")
# pickle.dump(blockchain, pickle_out)
# pickle_out.close()

pickle_in = open(routToFile, "rb")
blockchain = pickle.load(pickle_in)


#################################################################################

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(previous_hash)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'validator': block['validator'],
        'previous_hash': block['previous_hash'],
    }

    pickle_out = open(routToFile, "wb")
    pickle.dump(blockchain, pickle_out)
    pickle_out.close()

    return jsonify(response), 200


#################################################################################

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['data']

    for node in blockchain.nodes:
        tmp = 'http://' + node + '/transactions_for_node'
        requests.post(tmp, json=values)

    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['data'])

    response = {'message': 'Transaction will be added to Block', 'index': index}
    return jsonify(response), 201


#################################################################################

@app.route('/transactions_for_node', methods=['POST'])
def node_transaction():
    values = request.get_json()
    required = ['data']

    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['data'])

    response = {'message': 'Transaction will be added to Block', 'index': index}
    return jsonify(response), 201


#################################################################################

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
        'transactions': blockchain.current_transactions,
    }
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


#################################################################################


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

# python r.py --port=1337
