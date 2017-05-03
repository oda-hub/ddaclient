import json
import ast
import ddosaclient as dc
import discover_docker

c=discover_docker.DDOSAWorkerContainer()
r=dc.RemoteDDOSA(c.url)\
        .query(target="ii_skyimage",
               modules=["ddosa","git://ddosadm"],
               assume=['ddosa.ScWData(input_scwid="066500220010.001")'])

print r["result"]

print r.keys()

data=ast.literal_eval(str(r['data']))
        
json.dump(data,open("data.json","w"), sort_keys=True, indent=4, separators=(',', ': '))
