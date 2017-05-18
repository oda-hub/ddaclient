from __future__ import print_function

import requests
import os

import imp
import ast
import json

from simple_logger import log

import discover_docker

class WorkerException(Exception):
    pass

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

        data=ast.literal_eval(str(r['data']))

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
    default_modules=["ddosa","ddosadm"]
    default_assume=["ddosadm.DataSourceConfig(use_store_files=False)"]

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

    def prepare_request(self,target,modules=[],assume=[]):
        return dict(url=self.service_url+"/api/v1.0/"+target,
                    params=dict(modules=",".join(self.default_modules+modules),
                                assume=",".join(self.default_assume+assume)))

    def poke(self):
        return self.query("poke")

    def query(self,target,modules=[],assume=[]):
        try:
            p=self.prepare_request(target,modules,assume)
            response=requests.get(p['url'],p['params'],auth=self.secret.get_auth())
        except Exception as e:
            log("exception in request",e,logtype="error")
            raise

        try:
            return DDOSAproduct(response.json(),self.ddcache_root_local)
        except Exception as e:
            log("exception exctacting json:",e)
            log("raw content: ",response.content,logtype="error")
            raise WorkerException(repr(e)+"\nno json was produced!\nraw output:\n\n"+response.content)
            


    def __repr__(self):
        return "[%s: direct %s]"%(self.__class__.__name__,self.service_url)

class AutoRemoteDDOSA(RemoteDDOSA):
    def __init__(self,config_version=None):
        if config_version=="docker_any":
            c=discover_docker.DDOSAWorkerContainer()

            url=c.url
            ddcache_root_local=c.ddcache_root
            print("managed to read from docker:")
        elif 'DDOSA_WORKER_URL' in os.environ:
            url=os.environ['DDOSA_WORKER_URL']
            ddcache_root_local=""
        else:
            if config_version is None:
                if 'DDOSA_WORKER_VERSION' in os.environ:
                    config_version=os.environ['DDOSA_WORKER_VERSION']
                else:
                    config_version="devel"

            print("from config:",config_version)

            if config_version=="":
                config_suffix=''
            else:
                config_suffix='_'+config_version

            config_fn='/home/isdc/savchenk/etc/ddosa-docker/config%s.py'%config_suffix
            print(":",config_fn)

            ddosa_config = imp.load_source('ddosa_config', config_fn)

            ddcache_root_local=ddosa_config.ddcache_root_local
            url=ddosa_config.url

        print("url:",url)
        print("ddcache_root:",ddcache_root_local)

        super(AutoRemoteDDOSA,self).__init__(url,ddcache_root_local)



class HerdedDDOSA(RemoteDDOSA):
    def __repr__(self):
        return "[%s: herder %s]"%(self.__class__.__name__,self.service_url)

    def query(self):
        raise Exception("not implemented!")

