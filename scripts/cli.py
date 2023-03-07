
import instantcli
import renew
import json
instantcli.post_call = lambda result: print(json.dumps(result, default=lambda x: x.to_dict()))

instantcli.load_module( renew)
instantcli.cli()
