import json
import ast
import ddosaclient as dc
import discover_docker

c=discover_docker.DDOSAWorkerContainer()
r=dc.RemoteDDOSA(c.url)\
        .query(target="ii_skyimage",
               modules=["ddosa","git://ddosadm"],
               assume=['ddosa.ScWData(input_scwid="066500220010.001")',
                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

print r["result"]

print r.keys()

data=ast.literal_eval(str(r['data']))
        
json.dump(data,open("data.json","w"), sort_keys=True, indent=4, separators=(',', ': '))
print "jsonifiable data dumped to data.json"

print "cached object in",r['cached_path']

for k,v in data.items():
    try:
        if v[0]=="DataFile":
            print "data file attached:",k,(r['cached_path'][0].replace("data/ddcache",c.ddcache_root)+"/"+v[1]).replace("//","/")
    except:
        pass
