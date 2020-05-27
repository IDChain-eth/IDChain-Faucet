import os
import time
import json
import base64
import hashlib
import threading
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
import ed25519
from flask import Flask, request, jsonify

SKIP_LINKS = 0
BRIGHTID_NODE = 'http://test.brightid.org/brightid/v4'
VERIFICATIONS_URL = BRIGHTID_NODE + '/verifications/idchain/'
OPERATION_URL = BRIGHTID_NODE + '/operations/'
DISTRIBUTION_ADDRESS = '0x6E39d7540c2ad4C18Eb29501183AFA79156e79aa'
DISTRIBUTION_ABI = '[{"inputs": [{"internalType": "address payable", "name": "beneficiary", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "name": "claim", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "previousOwner", "type": "address"}, {"indexed": true, "internalType": "address", "name": "newOwner", "type": "address"}], "name": "OwnershipTransferred", "type": "event"}, {"inputs": [], "name": "renounceOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "addr", "type": "address"}], "name": "setBrightid", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "_claimable", "type": "uint256"}], "name": "setClaimable", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}], "name": "transferOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"stateMutability": "payable", "type": "receive"}, {"inputs": [], "name": "brightid", "outputs": [{"internalType": "contract BrightID", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "claimable", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "claimed", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}]'
BRIGHTID_ADDRESS = '0x72a70314C3adD56127413F78402392744af4EF64'
BRIGHTID_ABI = '[{"anonymous": false, "inputs": [{"indexed": false, "internalType": "contract IERC20", "name": "supervisorToken", "type": "address"}, {"indexed": false, "internalType": "contract IERC20", "name": "proposerToken", "type": "address"}], "name": "MembershipTokensSet", "type": "event"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "previousOwner", "type": "address"}, {"indexed": true, "internalType": "address", "name": "newOwner", "type": "address"}], "name": "OwnershipTransferred", "type": "event"}, {"inputs": [{"internalType": "bytes32", "name": "context", "type": "bytes32"}, {"internalType": "address[]", "name": "addrs", "type": "address[]"}, {"internalType": "uint8", "name": "v", "type": "uint8"}, {"internalType": "bytes32", "name": "r", "type": "bytes32"}, {"internalType": "bytes32", "name": "s", "type": "bytes32"}], "name": "propose", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "addr", "type": "address"}], "name": "Proposed", "type": "event"}, {"inputs": [], "name": "renounceOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "contract IERC20", "name": "_supervisorToken", "type": "address"}, {"internalType": "contract IERC20", "name": "_proposerToken", "type": "address"}], "name": "setMembershipTokens", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "uint256", "name": "_waiting", "type": "uint256"}, {"internalType": "uint256", "name": "_timeout", "type": "uint256"}], "name": "setTiming", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [], "name": "start", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [], "name": "Started", "type": "event"}, {"inputs": [], "name": "stop", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [{"indexed": false, "internalType": "address", "name": "stopper", "type": "address"}], "name": "Stopped", "type": "event"}, {"anonymous": false, "inputs": [{"indexed": false, "internalType": "uint256", "name": "waiting", "type": "uint256"}, {"indexed": false, "internalType": "uint256", "name": "timeout", "type": "uint256"}], "name": "TimingSet", "type": "event"}, {"inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}], "name": "transferOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "addr", "type": "address"}], "name": "Verified", "type": "event"}, {"inputs": [{"internalType": "bytes32", "name": "context", "type": "bytes32"}, {"internalType": "address[]", "name": "addrs", "type": "address[]"}], "name": "verify", "outputs": [], "stateMutability": "nonpayable", "type": "function"}, {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "history", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "isRevoked", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "name": "proposals", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "proposerToken", "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "stopped", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "supervisorToken", "outputs": [{"internalType": "contract IERC20", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "timeout", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "verifications", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [], "name": "waiting", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]'
RPC_URL = 'wss://idchain.one/ws/'
SPONSORSHIP_PRIVATEKEY = ''
NOT_FOUND = 'contextId not found'
NOT_SPONSORED = 'user is not sponsored'
NOT_VERIFIED = 'user can not be verified for this context'
CONTEXT = 'idchain'
CHAINID = 74
GAS = 500000
GAS_PRICE = 10
RELAYER_ADDRESS = '0x0df7eDDd60D613362ca2b44659F56fEbafFA9bFB'
RELAYER_PRIVATE = ''
WAITING_TIME = 15
PROCESSED_FILE = 'processed.txt'
CHECK_NUM = 20
CHECK_PERIOD = 10

w3 = Web3(Web3.WebsocketProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
brightid = w3.eth.contract(address=BRIGHTID_ADDRESS, abi=BRIGHTID_ABI)
distribution = w3.eth.contract(address=DISTRIBUTION_ADDRESS, abi=DISTRIBUTION_ABI)
nonce = w3.eth.getTransactionCount(RELAYER_ADDRESS)

def verify(addr):
    global nonce
    addr = Web3.toChecksumAddress(addr)
    block = brightid.functions.verifications(addr).call()
    if block > 0:
        print('{} is verified'.format(addr))
        return
    data = requests.get(VERIFICATIONS_URL + addr + '?signed=eth').json()
    data = data['data']
    data['contextIds'] = list(map(Web3.toChecksumAddress, data['contextIds']))
    print('proposing {}'.format(addr))
    tx = brightid.functions.propose(
        '0x' + CONTEXT.encode('ascii').hex(),
        data['contextIds'],
        data['sig']['v'],
        '0x' + data['sig']['r'],
        '0x' + data['sig']['s']
    ).buildTransaction({
        'chainId': CHAINID,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
        'nonce': nonce,
    })
    nonce += 1
    signed_txn = w3.eth.account.sign_transaction(tx, private_key=RELAYER_PRIVATE)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    print('waiting {}'.format(addr))
    time.sleep(WAITING_TIME)
    print('verifing {}'.format(addr))
    tx = brightid.functions.verify(
        '0x' + CONTEXT.encode('ascii').hex(),
        data['contextIds']
    ).buildTransaction({
        'chainId': CHAINID,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
        'nonce': nonce,
    })
    signed_txn = w3.eth.account.sign_transaction(tx, private_key=RELAYER_PRIVATE)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    nonce += 1
    print('{} verified'.format(addr))

def sponsor(addr):
    data = requests.get(VERIFICATIONS_URL + addr).json()
    if 'errorMessage' not in data or data['errorMessage'] != NOT_SPONSORED:
        print('{} is sponsored'.format(addr))
        return
    signing_key = ed25519.SigningKey(base64.b64decode(SPONSORSHIP_PRIVATEKEY))
    message = bytes('Sponsor,idchain,' + addr, 'ascii');
    sig = signing_key.sign(message)
    sig = base64.b64encode(sig).decode('ascii')
    m = hashlib.sha256()
    m.update(message)
    _key = base64.b64encode(m.digest()).decode('ascii')
    _key = _key.replace('+', '-').replace('/', '_').replace('=', '')
    r = requests.put(OPERATION_URL + _key, json.dumps({
        '_key': _key,
        'name': 'Sponsor',
        'context': 'idchain',
        'contextId': addr,
        'sig': sig,
        'v': 4
    }))
    assert r.text == '' and r.status_code == 204, 'error in sponsoring'
    for i in range(10):
        print('waiting for sponsor operation get applied')
        time.sleep(10)
        data = requests.get(VERIFICATIONS_URL + addr).json()
        if 'errorMessage' not in data or data['errorMessage'] != NOT_SPONSORED:
            print('{} sponsored'.format(addr))
            return
    raise Exception('sponsoring failed')

def claim(addrs):
    global nonce
    claimed = 0
    addrs = list(map(Web3.toChecksumAddress, addrs))
    for addr in addrs:
        claimed += distribution.functions.claimed(addr).call()

    claimable = distribution.functions.claimable().call()
    if claimable - claimed <= 0:
        print('{} claimed {} tokens before'.format(addrs, claimed/10**18))
        return
    tx = distribution.functions.claim(
        addrs[0],
        claimable - claimed
    ).buildTransaction({
        'chainId': CHAINID,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
        'nonce': nonce,
    })
    signed_txn = w3.eth.account.sign_transaction(tx, private_key=RELAYER_PRIVATE)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    nonce += 1
    print('{} claimed {} tokens'.format(addrs, (claimable - claimed)/10**18))

def process(addr):
    addr = addr.lower()
    print('processing {}'.format(addr))
    for i in range(CHECK_NUM):
        data = requests.get(VERIFICATIONS_URL + addr).json()
        if 'errorMessage' not in data or data['errorMessage'] != NOT_FOUND:
            break
        print('{} not found'.format(addr))
        time.sleep(CHECK_PERIOD)
    else:
        print('{} monitoring expired'.format(addr))
        return
    sponsor(addr)
    data = requests.get(VERIFICATIONS_URL + addr).json()
    if 'errorMessage' in data:
        print(addr, data['errorMessage'])
        return
    verify(addr)
    claim(data['data']['contextIds'])

app = Flask(__name__)
@app.route('/claim', methods=['POST'])
def claim_endpoint():
    addr = request.json.get('addr', None)
    if not addr:
        return jsonify({'success': False})
    threading.Thread(target=process, args=(addr,)).start()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='localhost', port=5000)
