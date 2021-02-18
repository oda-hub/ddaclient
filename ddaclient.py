import requests
import os
import urllib.request, urllib.parse, urllib.error


import imp
import ast
import time
import json

import traceback

import re

import logging

from pscolors import render

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

def log(*a,**aa):
    logger.info(repr((a,aa)))


class UnknownDDABackendProblem(Exception):
    pass

class AnalysisDelegatedException(Exception):
    def __init__(self, delegation_state):
        self.delegation_state = delegation_state

    def __repr__(self):
        return "[%s: %s]"%(self.__class__.__name__, self.delegation_state)

class AnalysisException(Exception):
    @classmethod
    def from_dda_analysis_exceptions(cls,analysis_exceptions):
        obj=cls("found analysis exceptions", analysis_exceptions)
        obj.exceptions=[]
        for node_exception in analysis_exceptions:
            logger.error("found analysis exception: %s", node_exception)

            if isinstance(node_exception, list) and len(node_exception)==2:
                node,exception=node_exception
                exception=exception.strip()
            else:
                try:
                    node,exception=re.match("\('(.*?)',(.*)\)",node_exception).groups()
                    exception=exception.strip()
                except TypeError:
                    raise Exception("unable to interpret node exception:",node_exception)

            obj.exceptions.append(dict(node=node,exception=exception,exception_kind="handled"))
        return obj

    @classmethod
    def from_dda_unhandled_exception(cls, unhandled_exception):
        obj = cls("found unhandled analysis exceptions", unhandled_exception)
        obj.exceptions = [dict([('kind',"unhandled")]+list(unhandled_exception.items()))]
        return obj

    @classmethod
    def from_graph_exception(cls, graph_exception):
        obj = cls("found graph exception", graph_exception)
        obj.exceptions = [graph_exception]
        return obj

    def __repr__(self):
        r = super().__repr__()
        r += "\n\nembedded exceptions"
        for exception in self.exceptions:
            if 'node' in exception:
                r += "in node %s: %s"%(exception['node'],exception['exception'])
            else:
                r += "no node %s"%repr(exception)
        return r

class WorkerException(Exception):
    def __init__(self,comment,content=None,product_exception=None,worker_output=None):
        self.comment=comment
        self.content=content
        self.product_exception=product_exception
        self.worker_output=worker_output

    def __repr__(self):
        r=self.__class__.__name__+": "+self.comment
        if self.worker_output:
            r+="\n\nWorker output:\n"+self.worker_output

    def display(self):
        logger.info(self)
        try:
            log(json.loads(self.content)['result']['output'])
        except Exception as e:
            log("detailed output display not easy")


class Secret(object):
    @property
    def secret_location(self):
        if 'DDA_SECRET_LOCATION' in os.environ:
            return os.environ['DDA_SECRET']
        else:
            return 

    def get_auth(self):
        username = None
        password = None

        tried = {}
        for n, m in [
                    ("env", lambda:os.environ.get("DDA_TOKEN").strip()),
                    ("env-usertoken", lambda:os.environ.get("DDA_USER_TOKEN").strip()),
                    ("file-home", lambda:open(os.environ['HOME']+"/.secret-dda-client").read().strip()),
                    ("file-env-fn", lambda:open(os.environ['DDA_SECRET']).read().strip()),
                    ]:
            try:
                username = "remoteintegral"
                password = m()
                break
            except Exception as e:
                logger.debug(f"failed auth method {n} {e}")
                tried[n] = repr(e)

        if password is None:
            logger.error(f"no credentials, tried: {tried}; will asssume plain")
            password = ""

        return requests.auth.HTTPBasicAuth(username, password)


class DDAproduct(object):
    def __init__(self,dda_worker_response, ddcache_root_local):
        self.ddcache_root_local=ddcache_root_local
        self.interpret_dda_worker_response(dda_worker_response)

    def interpret_dda_worker_response(self,r):
        self.raw_response = r

        logger = logging.getLogger(self.__class__.__name__)

        logger.debug("%s to parse \033[34m%s\033[0m", self, r["result"])

        logger.info("found result keys: %s",list(r.keys()))

        try:
            #data=ast.literal_eval(repr(r['data']))
            data=r['data']
        except ValueError:
            log("failed to interpret data \"",r['data'],"\"")
            log(r['data'].__class__)
            log(list(r['data'].keys()))
            open('tmp_data_dump.json','w').write(repr(r['data']))
            raise

        if r['exceptions']!=[] and r['exceptions']!='' and r['exceptions'] is not None:
            if r['exceptions']['exception_type']=="delegation":

                #if 'delegation_state' not in r['exceptions']:
                    #json.dump(r['exceptions'], open("exception.yaml", "wt"))
                    #raise Exception("exception is delegation but does not contain delegation state! dumped")

                raise AnalysisDelegatedException(r['exceptions'].get('delegation_state', 'unknown'))

            if r['exceptions']['exception'][0] == 'dataanalysis.core.AnalysisException':
                raise AnalysisException.from_dda_analysis_exceptions([r['exceptions']['exception']])

            raise AnalysisException.from_dda_unhandled_exception(r['exceptions'])

        if data is None:
            raise WorkerException("data is None, the analysis failed unexcplicably")
        
        if not isinstance(r['cached_path'], list):
            raise UnknownDDABackendProblem(f"cached_path in the response should be list, but is {r['cached_path'].__class__} : {r['cached_path']}")



        selected_cached_paths = [ c for c in r['cached_path'] if "data/reduced/ddcache" in c ]
        logger.info("ALL cached path: %s\n vs selected %s", r['cached_path'], selected_cached_paths)

                        
        if len(selected_cached_paths) > 1:
            raise UnknownDDABackendProblem(f"multiple entries in cached path for the object {selected_cached_paths}")
        elif len(selected_cached_paths) == 1:
            local_cached_path = selected_cached_paths[0].replace("data/reduced/ddcache", self.ddcache_root_local)
            logger.info("cached object in %s => %s", selected_cached_paths[0], local_cached_path)
        else:
            local_cached_path = None
            logger.warning("no cached path in this object")

        key = time.strftime('%Y-%m-%dT%H-%M-%S')
        json.dump(data,open(f"data_{key}.json","w"), sort_keys=True, indent=4, separators=(',', ': '))
        logger.info(f"jsonifiable data dumped to data_{key}.json")

        if local_cached_path is not None:
            for k,v in list(data.items()):
                logger.info("setting attribute %s", k)
                setattr(self, k, v)

                if isinstance(v, list) and len(v)>0 and v[0] == "DataFile":

                    local_fn=os.path.join(local_cached_path, v[1]).replace("//","/")+".gz"
                    log("data file attached:",k,local_fn)
                    setattr(self,k,local_fn)
        else:
            logger.warning("\033[31mNO LOCAL CACHE PATH\033[0m which might be a problem")

        if 'analysis_exceptions' in data and data['analysis_exceptions']!=[]:
            raise AnalysisException.from_dda_analysis_exceptions(data['analysis_exceptions'])



class RemoteDDA:
    default_modules = ["git://ddosa"]
    default_assume = []  # type: list
    #"ddadm.DataSourceConfig(use_store_files=False)"] if not ('SCWDATA_SOURCE_MODULE' in os.environ and os.environ['SCWDATA_SOURCE_MODULE']=='ddadm') else []

    def __init__(self,service_url,ddcache_root_local):
        self.service_url = service_url
        self.ddcache_root_local = ddcache_root_local

        if ddcache_root_local is None:
            raise Exception(f"unable to setup {self} without ddcache_root_local")

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

    def prepare_request(self,target,modules=[],assume=[],inject=[],prompt_delegate=True,callback=None):
        log("modules", ",".join(modules))
        log("assume", ",".join(assume))
        log("service url:",self.service_url)
        log("target:", target)
        log("inject:",inject)

        if prompt_delegate:
            api_version = "v2.0"
        else:
            api_version = "v1.0"

        args=dict(url=self.service_url+"/api/"+api_version+"/"+target,
                    params=dict(modules=",".join(self.default_modules+modules),
                                assume=",".join(self.default_assume+assume),
                                inject=json.dumps(inject),
                                ))

        if callback is not None:
            args['params']['callback']=callback
        
        if 'OPENID_TOKEN' in os.environ:
            args['params']['token']=os.environ['OPENID_TOKEN']

        return args


    def poke(self):
        return self.query("poke")

    def query(self,target,modules=[],assume=[],inject=[],prompt_delegate=True,callback=None):
        n_retries = getattr(self, 'n_retries', 10)
        for i in reversed(range(n_retries)):
            try:
                return self._query(target, modules, assume, inject, prompt_delegate, callback)
            except AnalysisException as e:
                logger.info("passing through analysis exception: %s", e)
                raise
            except AnalysisDelegatedException as e:
                logger.info("passing through delegated exception: %s", e)
                raise
            except Exception as e:
                logger.exception("\033[31msomething failed in query: %s\033[0m, %s / %s attempts left", e, i, n_retries)
                if i == 0:
                    raise
                else:
                    time.sleep(5)

        raise RuntimeError("we should not be here")
                


    def _query(self,target,modules=[],assume=[],inject=[],prompt_delegate=True,callback=None):
        key = time.strftime('%Y-%m-%dT%H-%M-%S')

        try:
            p=self.prepare_request(target,modules,assume,inject,prompt_delegate,callback)
            url=p['url']

            if any(["osa11" in module for module in modules]): # nogood patch, only for 1.2
                logger.info("request will be sent to OSA11")
                url=url.replace("interface-worker","interface-worker-osa11")
            else:
                logger.info("request will be sent to OSA10")

            logger.info("request to pipeline: %s",p)
            logger.info("request to pipeline: %s", url+"/"+urllib.parse.urlencode(p['params']))
            response = requests.get(url,p['params'],auth=self.secret.get_auth())
            logger.debug(response.text)
        except Exception as e:
            logger.error("exception in request %s", e)
            raise

        if target == "poke":
            logger.info("poke did not raise an exception, which is success!")
            return

        try:
            response_json=response.json()
            return DDAproduct(response_json, self.ddcache_root_local)
        except WorkerException as e:
            logger.error("problem interpretting request: %s", e)
            logger.error("raw content: %s", response.text)
            open(f"tmp_WorkerException_response_content-{time.strftime('%Y-%m-%dT%H-%M-%S')}.txt","wt").write(response.text)
            worker_output=None
            if "result" in response.json():
                if "output" in response.json()['result']:
                    worker_output=response.json()['result']['output']
                    open("tmp_response_content_result_output.txt", "w").write(worker_output)
                    for l in worker_output.splitlines():
                        logger.warning(f"worker >> {l}")

            raise WorkerException("no reasonable response!",content=response.content,worker_output=worker_output,product_exception=e)
        except AnalysisException as e:
            logger.info("passing through analysis exception: %s", e)
            raise
        except AnalysisDelegatedException as e:
            logger.info("passing through delegated exception: %s", e)
            raise
        except Exception as e:
            traceback.print_exc()
            logger.error("some unknown exception in response %s", repr(e))

            fn = f"tmp_Exception_response_content-{key}.txt"

            logger.error("raw response stored to %s", fn)
            open(fn, "wt").write(response.text)

            open(f"tmp_Exception_comment-{key}.json", "wt").write(json.dumps({
                                'exception': repr(e),
                                'tb': traceback.format_stack(),
                                'fexception': traceback.format_exc(),
                            }))

            raise Exception(f"UNKNOWN exception in worker {e}, response was {response.text[:200]}..., stored as {fn}")

    def __repr__(self):
        return "[%s: direct %s]"%(self.__class__.__name__,self.service_url)

class AutoRemoteDDA(RemoteDDA):

    def from_env(self,config_version):
        url = os.environ.get('DDA_INTERFACE_URL', os.environ.get('DDA_WORKER_URL'))

        if url is None:
            raise RuntimeError("DDA_INTERFACE_URL variable should contain url")

        ddcache_root_local = os.environ.get('INTEGRAL_DDCACHE_ROOT', os.path.join(os.getcwd(), "local-ddcache"))
        return url, ddcache_root_local

    def discovery_methods(self):
        return [
                    'from_env',
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

        logger.info("discovered DDA service: %s local cache %s", url, ddcache_root_local)


        log("url:",url)
        log("ddcache_root:",ddcache_root_local)

        super().__init__(url,ddcache_root_local)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='client to remote dda combinator')
    parser.add_argument('target')
    parser.add_argument('-m',dest='modules',action='append',default=[])
    parser.add_argument('-a',dest='assume',action='append',default=[])
    parser.add_argument('-i',dest='inject',action='append',default=[])
    parser.add_argument('-D',dest='prompt_delegate',action='store_true',default=True)
    parser.add_argument('-v',dest='verbose',action='store_true',default=False)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)


    if args.target == "poke":

        AutoRemoteDDA().poke()

    else:

        logger.info("target: %s",args.target)
        logger.info("modules: %s",args.modules)
        logger.info("assume: %s",args.assume)
        
        inject=[]
        for inject_fn in args.inject:
            inject.append(json.load(open(inject_fn)))

        log("inject: %s",inject)

        try:
            AutoRemoteDDA().query(
                    args.target,
                    args.modules,
                    args.assume,
                    inject=inject,
                    prompt_delegate=args.prompt_delegate,
                    )
        except AnalysisDelegatedException:
            logger.info(render("{MAGENTA}analysis delegated{/}"))

if __name__ == '__main__':
    main()

