
import instantcli
import renew
import json
from pprint import pprint

def printme(result):
    pprint(result)

instantcli.post_call = printme

instantcli.load_module( renew)
instantcli.cli()
