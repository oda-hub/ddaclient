

import json
import ast
import ddosaclient as dc
import discover_docker
import imp

try:
    c=discover_docker.DDOSAWorkerContainer()

    url=c.url
    ddcache_root_local=c.ddcache_root
    print("managed to read from docker:")
except Exception as e:
    print("failed to read from docker, will try config:")

    ddosa_config = imp.load_source('ddosa_config', '/home/isdc/savchenk/etc/ddosa-docker/config.py')

    ddcache_root_local=ddosa_config.ddcache_root_local
    url=ddosa_config.url

print("url:",url)
print("ddcache_root:",ddcache_root_local)

r=dc.RemoteDDOSA(url)\
        .query(target="Mosaic",
               modules=["ddosa","git://ddosadm","git://osahk","git://mosaic",'git://rangequery'],
               assume=['mosaic.ScWImageList(\
                                        input_scwlist=\
                                            rangequery.TimeDirectionScWList(\
                                                use_coordinates=dict(RA=83,DEC=22,radius=5),\
                                                use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                                                use_max_pointings=50 \
                                            )\
                                        )\
                                        ',
                       'mosaic.Mosaic(use_pixdivide=4)',
                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

print(r["result"])

print(list(r.keys()))

data=ast.literal_eval(str(r['data']))
        
json.dump(data,open("data.json","w"), sort_keys=True, indent=4, separators=(',', ': '))
print("jsonifiable data dumped to data.json")

print("cached object in",r['cached_path'])

for k,v in list(data.items()):
    try:
        if v[0]=="DataFile":
            print("data file attached:",k,(r['cached_path'][0].replace("data/ddcache",ddcache_root_local)+"/"+v[1]).replace("//","/")+".gz")
    except:
        # not iterable, or empty file
        pass
