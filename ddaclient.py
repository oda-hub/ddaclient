import requests
import os
import urllib.request
import urllib.parse
import urllib.error


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


def log(*a, **aa):
    logger.info(repr((a, aa)))


class NotAuthorizedOnDDA(Exception):
    pass


class UnknownDDABackendProblem(Exception):
    pass


class AnalysisDelegatedException(Exception):
    def __init__(self, delegation_state):
        self.delegation_state = delegation_state

    def __repr__(self):
        return "[%s: %s]" % (self.__class__.__name__, self.delegation_state)

class PermanentAnalysisException(Exception):
    pass

class AnalysisException(Exception):
    @classmethod
    def from_dda_analysis_exceptions(cls, analysis_exceptions):
        obj = cls("found analysis exceptions", analysis_exceptions)
        obj.exceptions = []
        for node_exception in analysis_exceptions:
            logger.error("found analysis exception: %s", node_exception)

            if isinstance(node_exception, list) and len(node_exception) == 2:
                node, exception = node_exception
                exception = exception.strip()
            else:
                try:
                    node, exception = re.match(
                        "\('(.*?)',(.*)\)", node_exception).groups()
                    exception = exception.strip()
                except TypeError:
                    raise Exception(
                        "unable to interpret node exception:", node_exception)

            obj.exceptions.append(
                dict(node=node, exception=exception, exception_kind="handled"))
        return obj

    @classmethod
    def from_dda_unhandled_exception(cls, unhandled_exception):
        obj = cls("found unhandled analysis exceptions", unhandled_exception)
        obj.exceptions = [
            dict([('kind', "unhandled")]+list(unhandled_exception.items()))]
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
                r += "in node %s: %s" % (exception['node'],
                                         exception['exception'])
            else:
                r += "no node %s" % repr(exception)
        return r


class WorkerException(Exception):
    def __init__(self, comment, content=None, product_exception=None, worker_output=None):
        self.comment = comment
        self.content = content
        self.product_exception = product_exception
        self.worker_output = worker_output

    def __repr__(self):
        r = self.__class__.__name__+": "+self.comment
        if self.worker_output:
            r += "\n\nWorker output:\n"+self.worker_output

    def display(self):
        logger.info(self)
        try:
            log(json.loads(self.content)['result']['output'])
        except Exception:
            log("detailed output display not easy")


class Secret(object):

    def discover_auth(self):
        if hasattr(self, '_username') and hasattr(self, '_password'):
            return

        username = None
        password = None
        auth_source = None

        tried = {}
        for auth_source, m in [
            ("env", lambda:os.environ.get("DDA_TOKEN").strip()),
            ("env-usertoken", lambda:os.environ.get("DDA_USER_TOKEN").strip()),
            ("file-env-fn",
             lambda:open(os.environ['DDA_SECRET_LOCATION']).read().strip()),
            ("file-env-fn-legacy",
             lambda:open(os.environ['DDA_SECRET']).read().strip()),
            ("file-home",
             lambda:open(os.environ['HOME']+"/.secret-dda-client").read().strip()),
        ]:
            try:
                username = "remoteintegral"
                password = m()
                break
            except Exception as e:
                logger.debug(f"failed auth method {auth_source} {e}")
                tried[auth_source] = repr(e)

        if password is None:
            logger.error(f"no credentials, tried: {tried}; will asssume plain")
            password = ""

        self._username = username
        self._password = password
        self._auth_source = auth_source

    def get_auth(self):
        self.discover_auth()
        return requests.auth.HTTPBasicAuth(self._username, self._password)


class DDAproduct(object):

    download_ddcache_files_if_necessary = True

    def __init__(self, dda_worker_response, ddcache_root_local, remote_dda):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.ddcache_root_local = ddcache_root_local
        self.remote_dda = remote_dda
        self.interpret_dda_worker_response(dda_worker_response)
        

    def download_ddcache_file(self, cached_path, filename, local_fn):
        self.logger.info("\033[31mdownloading extra file [%s : %s ] \033[0m", cached_path, filename)
        return self.remote_dda.download_ddcache_file(cached_path, filename, local_fn)

    def interpret_dda_worker_response(self, r):
        self.raw_response = r

        logger = self.logger

        logger.debug("%s to parse \033[34m%s\033[0m", self, r["result"])

        logger.info("found result keys: %s", list(r.keys()))

        try:
            # data=ast.literal_eval(repr(r['data']))
            data = r['data']
        except ValueError:
            log("failed to interpret data \"", r['data'], "\"")
            log(r['data'].__class__)
            log(list(r['data'].keys()))
            open('tmp_data_dump.json', 'w').write(repr(r['data']))
            raise

        if r['exceptions'] != [] and r['exceptions'] != '' and r['exceptions'] is not None:
            if r['exceptions']['exception_type'] == "delegation":

                # if 'delegation_state' not in r['exceptions']:
                #json.dump(r['exceptions'], open("exception.yaml", "wt"))
                #raise Exception("exception is delegation but does not contain delegation state! dumped")

                raise AnalysisDelegatedException(
                    r['exceptions'].get('delegation_state', 'unknown'))

            if r['exceptions']['exception'][0] == 'dataanalysis.core.AnalysisException':
                raise AnalysisException.from_dda_analysis_exceptions(
                    [r['exceptions']['exception']])

            raise AnalysisException.from_dda_unhandled_exception(
                r['exceptions'])

        if data is None:
            raise WorkerException(
                "data is None, the analysis failed unexcplicably")

        if not isinstance(r['cached_path'], list):
            raise UnknownDDABackendProblem(
                f"cached_path in the response should be list, but is {r['cached_path'].__class__} : {r['cached_path']}")

        selected_cached_paths = [
            c for c in r['cached_path'] if "data/reduced/ddcache" in c]
        logger.info("ALL cached path: %s\n vs selected %s",
                    r['cached_path'], selected_cached_paths)

        if len(selected_cached_paths) > 1:
            raise UnknownDDABackendProblem(
                f"multiple entries in cached path for the object {selected_cached_paths}")
        elif len(selected_cached_paths) == 1:
            selected_cached_path = selected_cached_paths[0]

            local_cached_path = os.path.join(
                self.ddcache_root_local,
                selected_cached_path.replace(
                    "data/reduced/ddcache", "").strip("/")
            )

            logger.info(
                "\033[32mself.ddcache_root_local: %s\033[0m", self.ddcache_root_local)
            logger.info("\033[32mprepared selected_cached_path: %s\033[0m",
                        selected_cached_path.replace("data/reduced/ddcache", "").strip("/"))
            logger.info("\033[32mcached object in %s => %s\033[0m",
                        selected_cached_path, local_cached_path)

            if not os.path.exists(local_cached_path):
                if self.download_ddcache_files_if_necessary:
                    os.makedirs(local_cached_path)
                else:
                    raise RuntimeError(
                        f"restored object can not be found in local space \"{local_cached_path}\": check local cache location: \"{self.ddcache_root_local}\"")
        else:
            local_cached_path = None
            logger.warning("no cached path in this object")

        key = time.strftime('%Y-%m-%dT%H-%M-%S')
        json.dump(data, open(f"data_{key}.json", "w"),
                  sort_keys=True, indent=4, separators=(',', ': '))
        logger.info(f"jsonifiable data dumped to data_{key}.json")

        if local_cached_path is not None:
            for k, v in list(data.items()):
                logger.info("setting attribute %s", k)
                setattr(self, k, v)

                if isinstance(v, list) and len(v) > 0 and v[0] == "DataFile":

                    local_fn = os.path.join(
                        local_cached_path, v[1]).replace("//", "/")+".gz"
                    log("data file attached:", k, local_fn)

                    if not os.path.exists(local_fn):
                        if self.download_ddcache_files_if_necessary:
                            local_fn = self.download_ddcache_file(cached_path=selected_cached_paths[0],
                                                       filename=v[1],
                                                       local_fn=local_fn,
                                                )
                            logger.info("restored in new location %s", local_fn)
                        else:
                            raise RuntimeError(
                                f"restored object file {local_fn} can not be found in local space \"{local_cached_path}\": check local cache location: \"{self.ddcache_root_local}\"")


                    setattr(self, k, local_fn)
        else:
            logger.warning(
                "\033[31mNO LOCAL CACHE PATH\033[0m which might be a problem")

        if 'analysis_exceptions' in data and data['analysis_exceptions'] != []:
            raise AnalysisException.from_dda_analysis_exceptions(
                data['analysis_exceptions'])


class RemoteDDA:
    default_modules = ["git://ddosa"]
    default_assume = []  # type: list
    # "ddadm.DataSourceConfig(use_store_files=False)"] if not ('SCWDATA_SOURCE_MODULE' in os.environ and os.environ['SCWDATA_SOURCE_MODULE']=='ddadm') else []

    def __init__(self, service_url, ddcache_root_local):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.service_url = service_url
        self.ddcache_root_local = ddcache_root_local

        if ddcache_root_local is None:
            raise Exception(
                f"unable to setup {self} without ddcache_root_local")

        self.secret = Secret()

    @property
    def service_url(self):
        return self._service_url

    @service_url.setter
    def service_url(self, service_url):
        if service_url is None:
            raise Exception("service url can not be None!")

        adapter = service_url.split(":")[0]
        if adapter not in ["http"]:
            raise Exception("adapter %s not allowed!" % adapter)
        self._service_url = service_url

    def prepare_request(self, target, modules=[], assume=[], inject=[], prompt_delegate=True, callback=None):
        log("modules", ",".join(modules))
        log("assume", ",".join(assume))
        log("service url:", self.service_url)
        log("target:", target)
        log("inject:", inject)

        if prompt_delegate:
            api_version = "v2.0"
        else:
            api_version = "v1.0"

        service_url = self.service_url
        
        if any(["integral_all_private" in module for module in modules]): 
            logger.info("sending request to private backend, the default")
        else: 
            if target != "poke":
                service_url = os.environ.get('DDA_INTERFACE_URL_PUBLIC_DATA', 'http://oda-dda-interface:8000') # get otherwise
                if service_url is None:
                    raise PermanentAnalysisException('not able to request public-only data currently')

        args = dict(url=service_url+"/api/"+api_version+"/"+target,
                    params=dict(modules=",".join(self.default_modules+modules),
                                assume=",".join(self.default_assume+assume),
                                inject=json.dumps(inject),
                                ))

        if callback is not None:
            args['params']['callback'] = callback

        if 'OPENID_TOKEN' in os.environ:
            args['params']['token'] = os.environ['OPENID_TOKEN']
        
        return args

    def download_ddcache_file(self, cached_path, filename, local_fn):
        local_fn_modified = local_fn
        #local_fn_modified = local_fn + ".recovered"

        self.logger.info("\033[31mdownloading extra file [ %s : %s ] to [ %s ] \033[0m", cached_path, filename, local_fn_modified)
        
        r = requests.get(
                     f"{self.service_url}/api/2.0/fetch-file",
                     params=dict(
                         cached_path=cached_path,
                         filename=filename
                     ),
                     auth=self.secret.get_auth()
                    )

        if r.status_code != 200:
            raise RuntimeError(f"unable to download file: {r} {r.text}")

        if os.path.exists(local_fn_modified):
            logger.warning("will download %s even though it already exists", local_fn_modified)
            #raise RuntimeError(f"will not download {local_fn_modified} since it already exists")

        os.makedirs(os.path.dirname(local_fn_modified), exist_ok=True)

        with open(local_fn_modified, "wb") as f:
            f.write(r.content)

        #TODO: storefile

        return local_fn_modified


    def poke(self):
        return self.query("poke")

    def query(self, target, modules=[], assume=[], inject=[], prompt_delegate=True, callback=None, sync=False):
        n_retries = getattr(self, 'n_retries', 10)

        for i in reversed(range(n_retries)):
            try:
                return self._query(target, modules, assume, inject, prompt_delegate, callback)
            except NotAuthorizedOnDDA as e:
                raise
            except (AnalysisException, PermanentAnalysisException) as e:
                logger.info("passing through analysis exception: %s", e)
                raise            
            except AnalysisDelegatedException as e:
                if not sync:
                    logger.info("passing through delegated exception: %s", e)
                    raise
            except Exception as e:
                logger.exception(
                    "\033[31msomething failed in query: %s\033[0m, %s / %s attempts left", e, i, n_retries)
                if i == 0:
                    raise
                else:
                    time.sleep(5)

        raise RuntimeError(
            f"request to DDA did not complete in {n_retries} tries!")

    def _query(self, target, modules=[], assume=[], inject=[], prompt_delegate=True, callback=None):
        key = time.strftime('%Y-%m-%dT%H-%M-%S')

        try:
            p = self.prepare_request(
                target, modules, assume, inject, prompt_delegate, callback)

            url = p['url']

            if any(["osa11" in module for module in modules]): 
                logger.info("request will be sent to OSA11")
                url = url.replace("interface-worker", "interface-worker-osa11")
            else:
                logger.info("request will be sent to OSA10")

            logger.info("request to pipeline with parameters: %s", p)
            logger.info("request to pipeline: %s", url+"?" +
                        urllib.parse.urlencode(p['params']))

            response = requests.post(
                url, data=json.dumps(p['params']), auth=self.secret.get_auth())

            logger.debug(response.text)
        except Exception as e:
            logger.error("exception in request %s", e)
            raise

        if response.status_code != 200:
            if response.status_code in [403, 401]:
                raise NotAuthorizedOnDDA(
                    f"used auth from {self.secret._auth_source}, user {self.secret._username}, raw response {response.text}")
            else:
                raise UnknownDDABackendProblem(
                    f"got unexpected response status {response.status_code}, raw response {response.text}")

        if target == "poke":
            logger.info(
                "poke did not raise an exception, which is success! poke details: %s", response.text)
            return

        try:
            response_json = response.json()
            return DDAproduct(response_json, self.ddcache_root_local, self)
        except WorkerException as e:
            logger.error("problem interpretting request: %s", e)
            logger.error("raw content: %s", response.text)
            open(
                f"tmp_WorkerException_response_content-{time.strftime('%Y-%m-%dT%H-%M-%S')}.txt", "wt").write(response.text)
            worker_output = None
            if "result" in response.json():
                if "output" in response.json()['result']:
                    worker_output = response.json()['result']['output']
                    open("tmp_response_content_result_output.txt",
                         "w").write(worker_output)
                    for l in worker_output.splitlines():
                        logger.warning(f"worker >> {l}")

            raise WorkerException("no reasonable response!", content=response.content,
                                  worker_output=worker_output, product_exception=e)
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

            raise Exception(
                f"UNKNOWN exception in worker {e}, response was {response.text[:200]}..., stored as {fn}")

    def __repr__(self):
        return "[%s: direct %s]" % (self.__class__.__name__, self.service_url)


class AutoRemoteDDA(RemoteDDA):

    def from_env(self, config_version):
        url = os.environ.get('DDA_INTERFACE_URL',
                             os.environ.get('DDA_WORKER_URL'))

        if url is None:
            raise RuntimeError("DDA_INTERFACE_URL variable should contain url")

        ddcache_root_local = os.environ.get(
            'INTEGRAL_DDCACHE_ROOT', os.path.join(os.getcwd(), "local-ddcache"))
        return url, ddcache_root_local

    def discovery_methods(self):
        return [
            'from_env',
        ]

    def __init__(self, config_version=None):

        methods_tried = []
        result = None
        for method in self.discovery_methods():

            try:
                result = getattr(self, method)(config_version)
            except Exception as e:
                methods_tried.append((method, e))

        if result is None:
            raise Exception(
                "all docker discovery methods failed, tried "+repr(methods_tried))

        url, ddcache_root_local = result

        logger.info("discovered DDA service: %s local cache %s",
                    url, ddcache_root_local)

        log("url:", url)
        log("ddcache_root:", ddcache_root_local)

        super().__init__(url, ddcache_root_local)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='client to remote dda combinator')
    parser.add_argument('target')
    parser.add_argument('-m', dest='modules', action='append', default=[])
    parser.add_argument('-a', dest='assume', action='append', default=[])
    parser.add_argument('-i', dest='inject', action='append', default=[])
    parser.add_argument('-D', dest='prompt_delegate',
                        action='store_true', default=True)
    parser.add_argument('-v', dest='verbose',
                        action='store_true', default=False)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    if args.target == "poke":

        AutoRemoteDDA().poke()

    else:

        logger.info("target: %s", args.target)
        logger.info("modules: %s", args.modules)
        logger.info("assume: %s", args.assume)

        inject = []
        for inject_fn in args.inject:
            inject.append(json.load(open(inject_fn)))

        log("inject: %s", inject)

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
