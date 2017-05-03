from __future__ import print_function

import requests
import StringIO
import json
import logging

def setup_logger():
    logger = logging.getLogger('root')
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.INFO)
    return logger

logger=setup_logger() # global logger, well

def log(*args, **kwargs):
    logtype = 'debug' if 'logtype' not in kwargs else kwargs['logtype']
    sep = ' ' if 'sep' not in kwargs else kwargs['sep']
    getattr(logger, logtype)(sep.join(str(a) for a in args))

class RemoteDDOSA(object):
    default_modules=["ddosadm"]
    default_assume=["ddosadm.DataSourceConfig(use_store_files=False)"]

    def __init__(self,service_url=None):
        self.service_url=service_url

    @property
    def service_url(self):
        return self._service_url

    @service_url.setter
    def service_url(self,service_url):
        self._service_url=service_url

    def prepare_request(self,target,modules=[],assume=[]):
        return dict(url=self.service_url+"/api/v1.0/"+target,
                    params=dict(modules=",".join(self.default_modules+modules),
                                assume=",".join(self.default_assume+assume)))

    def query(target,modules=[],assume=[]):
        try:
            p=self.prepare_request(target,modules,assume)
            r=requests.get(p['url'],p['params'])
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
