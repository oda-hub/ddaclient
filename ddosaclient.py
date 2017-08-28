from __future__ import print_function

import requests
import os
import urllib


import imp
import ast
import json

from simple_logger import log

try:
    import discover_docker
    docker_available=True
except ImportError:
    docker_available=False

class WorkerException(Exception):
    def __init__(self,comment,content=None,product_exception=None):
        self.comment=comment
        self.content=content
        self.product_exception=product_exception

    def __repr__(self):
        return self.__class__.__name__+": "+self.comment

    def display(self):
        log(repr(self))
        try:
            log(json.loads(self.content)['result']['output'])
        except Exception as e:
            log("detailed output display not easy")


class Secret(object):
    @property
    def secret_location(self):
        if 'DDOSA_SECRET' in os.environ:
            return os.environ['DDOSA_SECRET']
        else:
            return os.environ['HOME']+"/.secret-ddosa-client"

    def get_auth(self):
        username="remoteintegral" # keep separate from secrect to cause extra confusion!
        password=open(self.secret_location).read().strip()
        return requests.auth.HTTPBasicAuth(username, password)


class DDOSAproduct(object):
    def __init__(self,ddosa_worker_response,ddcache_root_local):
        self.ddcache_root_local=ddcache_root_local
        self.interpret_ddosa_worker_response(ddosa_worker_response)

    def interpret_ddosa_worker_response(self,r):
        self.raw_response=r

        print(self,r["result"])

        print("found result keys:",r.keys())

        try:
            #data=ast.literal_eval(repr(r['data']))
            data=r['data']
        except ValueError:
            print("failed to interpret data \"",r['data'],"\"")
            print(r['data'].__class__)
            print(r['data'].keys())
            open('tmp_data_dump.json','w').write(repr(r['data']))
            raise

        if data is None:
            raise WorkerException("data is None, the analysis failed")

        json.dump(data,open("data.json","w"), sort_keys=True, indent=4, separators=(',', ': '))
        print("jsonifiable data dumped to data.json")

        print("cached object in",r['cached_path'])

        for k,v in data.items():
            print("setting attribute",k)
            setattr(self,k,v)

            try:
                if v[0]=="DataFile":
                    local_fn=(r['cached_path'][0].replace("data/ddcache",self.ddcache_root_local)+"/"+v[1]).replace("//","/")+".gz"
                    print("data file attached:",k,local_fn)
                    setattr(self,k,local_fn)
            except Exception as e:
                pass


class RemoteDDOSA(object):
    default_modules=["git://ddosa","ddosadm"]
    default_assume=["ddosadm.DataSourceConfig(use_store_files=False)"] if not ('SCWDATA_SOURCE_MODULE' in os.environ and os.environ['SCWDATA_SOURCE_MODULE']=='ddosadm') else []

    def __init__(self,service_url,ddcache_root_local):
        self.service_url=service_url
        self.ddcache_root_local=ddcache_root_local

        self.secret=Secret()

    @property
    def service_url(self):
        return self._service_url

    @service_url.setter
    def service_url(self,service_url):
        if service_url is None:
            raise Exception("service url can not be None!")
        
        adapter=service_url.split(":")[0]
        if adapter not in ["http"]:
            raise Exception("adapter %s not allowed!"%adapter)
        self._service_url=service_url

    def prepare_request(self,target,modules=[],assume=[],inject=[]):
        log("modules", ",".join(modules))
        log("assume", ",".join(assume))
        log("service url:",self.service_url)
        log("target:", target)
        log("inject:",inject)
        args=dict(url=self.service_url+"/api/v1.0/"+target,
                    params=dict(modules=",".join(self.default_modules+modules),
                                assume=",".join(self.default_assume+assume),
                                inject=json.dumps(inject),
                                ))

        
        if 'OPENID_TOKEN' in os.environ:
            args['params']['token']=os.environ['OPENID_TOKEN']

        return args


    def poke(self):
        return self.query("poke")

    def query(self,target,modules=[],assume=[],inject=[]):
        try:
            p=self.prepare_request(target,modules,assume,inject)
            log("request to pipeline:",p)
            log("request to pipeline:",p['url']+"/"+urllib.urlencode(p['params']))
            response=requests.get(p['url'],p['params'],auth=self.secret.get_auth())
        except Exception as e:
            log("exception in request",e,logtype="error")
            raise

        try:
            response_json=response.json()
            return DDOSAproduct(response_json,self.ddcache_root_local)
        except WorkerException as e:
        #except Exception as e:
            log("exception exctacting json:",e)
            log("raw content: ",response.content,logtype="error")
            open("tmp_response_content.txt","w").write(response.content)
            raise WorkerException("no json was produced!",content=response.content,product_exception=e)
            


    def __repr__(self):
        return "[%s: direct %s]"%(self.__class__.__name__,self.service_url)

class AutoRemoteDDOSA(RemoteDDOSA):

    def from_docker(self,config_version):
        if config_version == "docker_any" and docker_available:
            c = discover_docker.DDOSAWorkerContainer()

            url = c.url
            ddcache_root_local = c.ddcache_root
            print("managed to read from docker:")
            return url,ddcache_root_local
        raise Exception("not possible to access docker")

    def from_env(self,config_version):
        url = os.environ['DDOSA_WORKER_URL']
        ddcache_root_local = os.environ['INTEGRAL_DDCACHE_ROOT']
        return url, ddcache_root_local

    def from_config(self,config_version):
        if config_version is None:
            if 'DDOSA_WORKER_VERSION' in os.environ:
                config_version = os.environ['DDOSA_WORKER_VERSION']
            else:
                config_version = "devel"

        print("from config:", config_version)

        if config_version == "":
            config_suffix = ''
        else:
            config_suffix = '_' + config_version

        config_fn = '/home/isdc/savchenk/etc/ddosa-docker/config%s.py' % config_suffix
        print(":", config_fn)

        ddosa_config = imp.load_source('ddosa_config', config_fn)

        ddcache_root_local = ddosa_config.ddcache_root_local
        url = ddosa_config.url

        return url, ddcache_root_local

    def discovery_methods(self):
        return [
                    'from_docker',
                    'from_env',
                    'from_config',
            ]


    def __init__(self,config_version=None):

        methods_tried=[]
        result=None
        for method in self.discovery_methods():

            try:
                result=getattr(self,method)(config_version)
            except Exception as e:
                methods_tried.append((method,e))

        if result is None:
            raise Exception("all docker discovery methods failed, tried "+repr(methods_tried))

        url, ddcache_root_local = result


        print("url:",url)
        print("ddcache_root:",ddcache_root_local)

        super(AutoRemoteDDOSA,self).__init__(url,ddcache_root_local)



class HerdedDDOSA(RemoteDDOSA):
    def __repr__(self):
        return "[%s: herder %s]"%(self.__class__.__name__,self.service_url)

    def query(self):
        raise Exception("not implemented!")

