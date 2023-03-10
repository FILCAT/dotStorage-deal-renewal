import asyncio
from web3 import Web3
import binascii
import subprocess
from cid import make_cid
import csv
import time
import sys
import json
import os
import time
import uuid

DealClientStorageRenewalAddress = "0x5972018edbecfff57f3f389146350f603d83fd72" # verified = true with some  data cap
DealClientStorageRenewalAddress = Web3.to_checksum_address(DealClientStorageRenewalAddress)

w3 = Web3(Web3.HTTPProvider('https://api.hyperspace.node.glif.io/rpc/v1'))
abi_json = "../out/DealClientStorageRenewal.sol/DealClientStorageRenewal.json"

w3wss_url = 'wss://wss.hyperspace.node.glif.io/apigw/lotus/rpc/v1'

try:
    abi = json.load(open(abi_json))['abi']
    bytecode = json.load(open(abi_json))['bytecode']['object']
except Exception:
    print("Run forge b to compile abi")
    raise

PA=w3.eth.account.from_key(os.environ['PRIVATE_KEY'])

curBlock = w3.eth.get_block('latest')

def getDeal():
    _id = b"\x05\xe3\xaf\x994\x10'\x9a\xc5\xe5\xaf+\xc6\t\xbf\x11\xf2\xc7\xdfZ\x89mW\x9c5\x03LBn\xc6\xe2\x19"
    print( getContract().functions.getDealRequestPub(_id).call())
    return getContract().functions.getDealRequestPub(_id).call()

def listenEvents():
    def handle_event(event):
        print(event.args.id)
        print( getContract().functions.getDealRequestPub(event.args.id).call())
        #print(event)

    w3wss = Web3(Web3.WebsocketProvider(w3wss_url))
    ContractFactory = w3wss.eth.contract(abi=abi)
    wscontract = ContractFactory(DealClientStorageRenewalAddress)
    latest = w3.eth.get_block('latest').number 
    oldestBlock =  latest - 30480
    event_filter = wscontract.events.DealProposalCreate().create_filter(fromBlock=oldestBlock, toBlock=latest)
    for event in event_filter.get_new_entries():
        handle_event(event)
    event_filter = wscontract.events.DealProposalCreate().create_filter(fromBlock="latest")
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
        time.sleep(1)

def runCommand(cmd):    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output = process.communicate()[0].decode('utf-8').strip()
    return output

def getCID(cid):
    #return bytes("bafk2bzaceanzppnlffioby4nac2hhjmrstzntqie3oid4ovq6zu4qhhjs4bvy", 'ascii')
    #return b'\x01\x81\xe2\x03\x92  \x05@\x88\xfbI\xe2/\xda7\xd3\t\rK\x17\xbe\x87\xae\xabp\xba\xc5\x8b=w\x95E\x12h\x11\x80=%'
    # Call the Go program to reverse the input string
    output = runCommand(['go', 'run', 'cidbytes.go', cid])
    #convert from [ 2 3 4 5] to [2,3,4,5] and parse with json.loads
    output = output.replace(" ", ",")
    ret_cid = bytes(json.loads(output))
    #ret_cid = bytes([0]) + ret_cid
    print(''.join(format(x, '02x') for x in ret_cid))
    return ret_cid

def getTxInfo():
    return { 'from': PA.address,
            'nonce': w3.eth.get_transaction_count(PA.address)}

def sendTx(tx):
    tx['maxPriorityFeePerGas'] = 200000 #max(tx['maxPriorityFeePerGas'], tx['maxFeePerGas']) # intermittently fails otherwise
    tx['maxFeePerGas'] = 200000 #max(tx['maxPriorityFeePerGas'], tx['maxFeePerGas']) # intermittently fails otherwise
    tx_create = w3.eth.account.sign_transaction(tx, PA._private_key)
    tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def deploy():
    DealClientStorageRenewal = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_info = getTxInfo()
    construct_txn = DealClientStorageRenewal.constructor().build_transaction(tx_info)
    tx_receipt = sendTx(construct_txn)
    print(f'Contract deployed at address: { tx_receipt.contractAddress.lower() }')


def getContract():
    ContractFactory = w3.eth.contract(abi=abi)
    contract = ContractFactory(DealClientStorageRenewalAddress)
    return contract

def isVerified(actorid):
    actorid = int(actorid)
    contract = getContract()
    return contract.functions.isVerifiedSP(actorid).call()


def submitcsvbatch(csv_filename):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        cids = []
        piece_sizes = []
        location_refs = []
        car_sizes = []
        for row in reader:
            cids.append( row['piece_cid'])
            piece_sizes.append(  row['piece_size'])
            location_refs.append( row['signed_url'])
            car_sizes.append(row['car_size'])
        x = createDealRequests(cids, piece_sizes, location_refs, car_sizes)
        print(x)


def submitcsv(csv_filename):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cid = row['piece_cid']
            piece_size = row['piece_size']
            location_ref = row['signed_url']
            car_size = row['car_size']
            x = createDealRequest(cid, piece_size, location_ref, car_size)
            print(x)

def testVerified():
    is_v = isVerified(5)
    assert(is_v)
    is_v = isVerified(234234)
    assert(not is_v)


def wait(blockNumber):
    wait_block_count = 0
    while True:
        curBlock = w3.eth.get_block('latest')
        if curBlock.number - blockNumber > wait_block_count:
            return
        time.sleep(1)

def createDealRequests(cids, piece_sizes, location_refs, car_sizes):
    labels = [cid for cid in cids ]
    CIDs = [getCID(cid) for cid in cids ]
    piece_sizes = [int(piece_size) for piece_size in piece_sizes ]
    car_sizes = [int(car_size) for car_size in car_sizes ]
    location_refs = [str(location_ref) for location_ref in location_refs]
    contract = getContract()
    tx_info = getTxInfo()
    tx = contract.functions.createDealRequests(CIDs, piece_sizes, location_refs, car_sizes, labels).build_transaction(tx_info)
    tx_receipt = sendTx(tx)
    wait(tx_receipt.blockNumber)
    return tx_receipt


def createDealRequest(cid, piece_size, location_ref, car_size):
    label = str(cid)
    CID = getCID(cid)
    print("cid ", cid)
    print("CID ", CID)
    piece_size = int(piece_size)
    car_size = int(car_size)
    location_ref = str(location_ref)
    contract = getContract()
    tx_info = getTxInfo()
    tx = contract.functions.createDealRequest(CID, piece_size, location_ref, car_size, label).build_transaction(tx_info)
    tx_receipt = sendTx(tx)
    wait(tx_receipt.blockNumber)
    return tx_receipt

def deleteSP(actor_id):
    actor_id = int(actor_id)
    contract = getContract()
    tx_info = getTxInfo()
    tx_receipt = sendTx(contract.functions.deleteSP(actor_id).build_transaction(tx_info))
    print("wait for confirmations")
    wait(tx_receipt.blockNumber)
    return True

def addVerifiedSP(actor_id):
    actor_id = int(actor_id)
    contract = getContract()
    tx_info = getTxInfo()
    tx_receipt = sendTx(contract.functions.addVerifiedSP(actor_id).build_transaction(tx_info))
    print("wait for confirmations")
    wait(tx_receipt.blockNumber)
    return True
    
def testAddRandomSP():
    actor_id = uuid.uuid1().int>>64
    print("Creating new actor", actor_id)
    is_v = isVerified(actor_id)
    assert(not is_v)
    print("Actor is not verified. Adding actor to verfied SP list")
    addVerifiedSP(actor_id)

    print("test the new actor is verified")
    is_v = isVerified(actor_id)
    assert(is_v)
