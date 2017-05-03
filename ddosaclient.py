from __future__ import print_function

import requests
import os

from simple_logger import log

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


class RemoteDDOSA(object):
    default_modules=["ddosa","ddosadm"]
    default_assume=["ddosadm.DataSourceConfig(use_store_files=False)"]

    def __init__(self,service_url):
        self.service_url=service_url

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

    def query(self,target,modules=[],assume=[]):
        try:
            p=self.prepare_request(target,modules,assume)
            r=requests.get(p['url'],p['params'],auth=self.secret.get_auth())
        except Exception as e:
            log("exception in request",e,logtype="error")
            return e
            
        try:
            return r.json()
        except Exception as e:
            log("exception exctacting json:",e)
            log("raw content: ",r.content,logtype="error")
            return r.content


    def __repr__(self):
        return "[%s: direct %s]"%(self.__class__.__name__,self.service_url)



class HerdedDDOSA(RemoteDDOSA):
    def __repr__(self):
        return "[%s: herder %s]"%(self.__class__.__name__,self.service_url)

    def query(self):
        raise Exception("not implemented!")

