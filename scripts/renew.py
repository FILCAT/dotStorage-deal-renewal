from web3 import Web3
import uuid
import time
import os
import json

w3 = Web3(Web3.HTTPProvider('https://api.hyperspace.node.glif.io/rpc/v1'))
abi_json = "../out/DealClientStorageRenewal.sol/DealClientStorageRenewal.json"
try:
    abi = json.load(open(abi_json))['abi']
    bytecode = json.load(open(abi_json))['bytecode']['object']
except Exception:
    print("Run forge b to compile abi")
    raise

PA=w3.eth.account.from_key(os.environ['PRIVATE_KEY'])

address = "0x6f50BA62BEafFE18145ef221ABf6D0A81B77f25D"
curBlock = w3.eth.get_block('latest')


def getTxInfo():
    return { 'from': PA.address,
            'nonce': w3.eth.get_transaction_count(PA.address)}

def sendTx(tx):
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
    contract = ContractFactory(address)
    return contract

def isVerified(actorId):
    contract = getContract()
    return contract.functions.isVerifiedSP(actorId).call()

def getSPs():
    contract = getContract()
    return contract.functions.verifiedSPs().call()


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
    
def testAddRandomSP():
    actor_id = uuid.uuid1().int>>64
    print("Creating new actor", actor_id)
    is_v = isVerified(actor_id)
    assert(not is_v)
    print("Actor is not verified. Adding actor to verfied SP list")

    contract = getContract()
    tx_info = getTxInfo()
    tx_receipt = sendTx(contract.functions.addVerifiedSP(actor_id).buildTransaction(tx_info))
    print("wait for confirmations")
    wait(tx_receipt.blockNumber)
    print("test the new actor is verified")
    is_v = isVerified(actor_id)
    assert(is_v)


#deploy()
#testAddRandomSP()
