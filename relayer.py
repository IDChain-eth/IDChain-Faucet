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
from config import *

w3 = Web3(Web3.WebsocketProvider(RPC_URL))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
brightid = w3.eth.contract(address=BRIGHTID_ADDRESS, abi=BRIGHTID_ABI)
distribution = w3.eth.contract(address=DISTRIBUTION_ADDRESS, abi=DISTRIBUTION_ABI)
nonce = w3.eth.getTransactionCount(RELAYER_ADDRESS)

def transact(f):
    global nonce
    tx = f.buildTransaction({
        'chainId': CHAINID,
        'gas': GAS,
        'gasPrice': GAS_PRICE,
        'nonce': nonce,
    })
    nonce += 1
    signed_txn = w3.eth.account.sign_transaction(tx, private_key=RELAYER_PRIVATE)
    w3.eth.sendRawTransaction(signed_txn.rawTransaction)
    receipt = w3.eth.waitForTransactionReceipt(signed_txn['hash'])
    assert receipt['status'], '{} failed'.format(tx)

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
    transact(brightid.functions.propose(
        '0x' + CONTEXT.encode('ascii').hex(),
        data['contextIds'],
        data['sig']['v'],
        '0x' + data['sig']['r'],
        '0x' + data['sig']['s']
    ))
    print('waiting {}'.format(addr))
    time.sleep(WAITING_TIME_AFTER_PROPOSING)
    print('verifing {}'.format(addr))
    transact(brightid.functions.verify(
        '0x' + CONTEXT.encode('ascii').hex(),
        data['contextIds']
    ))
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
    for i in range(SPONSOR_CHECK_NUM):
        print('waiting for sponsor operation get applied')
        time.sleep(SPONSOR_CHECK_PERIOD)
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
    transact(distribution.functions.claim(
        addrs[0],
        claimable - claimed
    ))
    print('{} claimed {} tokens'.format(addrs, (claimable - claimed)/10**18))

def process(addr):
    print('processing {}'.format(addr))
    # waiting for link
    for i in range(LINK_CHECK_NUM):
        data = requests.get(VERIFICATIONS_URL + addr).json()
        if 'errorMessage' not in data or data['errorMessage'] != NOT_FOUND:
            break
        print('{} not found'.format(addr))
        time.sleep(LINK_CHECK_PERIOD)
    else:
        print('{} monitoring expired'.format(addr))
        return
    sponsor(addr)
    data = requests.get(VERIFICATIONS_URL + addr).json()
    # return if user does not have BrightID verification
    # or there are other errors
    if 'errorMessage' in data:
        print(addr, data['errorMessage'])
        return
    verify(addr)
    claim(data['data']['contextIds'])

processing = {}
def _process(addr):
    if addr in processing:
        return
    processing[addr] = True
    try:
        process(addr)
    except:
        raise
    finally:
        del processing[addr]

app = Flask(__name__)
@app.route('/claim', methods=['POST'])
def claim_endpoint():
    addr = request.json and request.json.get('addr', '').lower()
    if not addr:
        return jsonify({'success': False})
    data = requests.get(VERIFICATIONS_URL + addr).json()
    contextIds = data.get('data', {}).get('contextIds', [])
    if contextIds and contextIds[0] != addr:
        e = 'This address is used before. Link a new address or use {} as your last linked address!'.format(contextIds[0])
        return jsonify({'success': False, 'error': e})
    threading.Thread(target=_process, args=(addr,)).start()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
