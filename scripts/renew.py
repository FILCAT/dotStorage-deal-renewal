from web3 import Web3
import csv
import json
import os
import time
import uuid

DealClientStorageRenewalAddress = "0x7f5D723287569d4e0B9e3A93f8306Acb665F02b1"

w3 = Web3(Web3.HTTPProvider('https://api.hyperspace.node.glif.io/rpc/v1'))
abi_json = "../out/DealClientStorageRenewal.sol/DealClientStorageRenewal.json"
try:
    abi = json.load(open(abi_json))['abi']
    bytecode = json.load(open(abi_json))['bytecode']['object']
except Exception:
    print("Run forge b to compile abi")
    raise

PA=w3.eth.account.from_key(os.environ['PRIVATE_KEY'])

curBlock = w3.eth.get_block('latest')


def getTxInfo():
    return { 'from': PA.address,
            'nonce': w3.eth.get_transaction_count(PA.address)}

def sendTx(tx):
    tx['maxPriorityFeePerGas'] = max(tx['maxPriorityFeePerGas'], tx['maxFeePerGas']) # intermittently fails otherwise
    tx['maxFeePerGas'] = max(tx['maxPriorityFeePerGas'], tx['maxFeePerGas']) # intermittently fails otherwise
    tx_create = w3.eth.account.sign_transaction(tx, PA.privateKey)
    tx_hash = w3.eth.send_raw_transaction(tx_create.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def deploy():
    DealClientStorageRenewal = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_info = getTxInfo()
    construct_txn = DealClientStorageRenewal.constructor().buildTransaction(tx_info)
    tx_receipt = sendTx(construct_txn)
    print(f'Contract deployed at address: { tx_receipt.contractAddress }')


def getContract():
    ContractFactory = w3.eth.contract(abi=abi)
    contract = ContractFactory(DealClientStorageRenewalAddress)
    return contract

def isVerified(actorid):
    actorid = int(actorid)
    contract = getContract()
    return contract.functions.isVerifiedSP(actorid).call()

def getSPs():
    contract = getContract()
    return contract.functions.verifiedSPs().call()

def submitcsvbatch(csv_filename):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        cids = []
        piece_sizes = []
        location_refs = []
        car_sizes = []
        for row in reader:
            print(row)
            cids.append( row['piece_cid'])
            piece_sizes.append(  row['piece_size'])
            location_refs.append( row['signed_url'])
            car_sizes.append(row.get("car_size", 0)) #TODO this is hard coded for now
        x = createDealRequests(cids, piece_sizes, location_refs, car_sizes)
        print(x)


def submitcsv(csv_filename):
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(row)
            cid = row['piece_cid']
            piece_size = row['piece_size']
            location_ref = row['signed_url']
            car_size = row.get("car_size", 0) #TODO this is hard coded for now
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
    CIDs = [bytes(cid, 'ascii') for cid in cids ]
    piece_sizes = [int(piece_size) for piece_size in piece_sizes ]
    car_sizes = [int(car_size) for car_size in car_sizes ]
    location_refs = [str(location_ref) for location_ref in location_refs]
    contract = getContract()
    tx_info = getTxInfo()
    tx = contract.functions.createDealRequests(CIDs, piece_sizes, location_refs, car_sizes).buildTransaction(tx_info)
    tx_receipt = sendTx(tx)
    wait(tx_receipt.blockNumber)
    return tx_receipt


def createDealRequest(cid, piece_size, location_ref, car_size):
    CID = bytes(cid, 'ascii')
    piece_size = int(piece_size)
    car_size = int(car_size)
    location_ref = str(location_ref)
    contract = getContract()
    tx_info = getTxInfo()
    tx = contract.functions.createDealRequest(CID, piece_size, location_ref, car_size).buildTransaction(tx_info)
    tx_receipt = sendTx(tx)
    wait(tx_receipt.blockNumber)
    return tx_receipt

def deleteSP(actor_id):
    actor_id = int(actor_id)
    contract = getContract()
    tx_info = getTxInfo()
    tx_receipt = sendTx(contract.functions.deleteSP(actor_id).buildTransaction(tx_info))
    print("wait for confirmations")
    wait(tx_receipt.blockNumber)
    return True

def addVerifiedSP(actor_id):
    actor_id = int(actor_id)
    contract = getContract()
    tx_info = getTxInfo()
    tx_receipt = sendTx(contract.functions.addVerifiedSP(actor_id).buildTransaction(tx_info))
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
