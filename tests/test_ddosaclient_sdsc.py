import pytest
import requests
import os
import time

import ddosaclient

scwsource_module="ddosa"
if 'SCWDATA_SOURCE_MODULE' in os.environ:
    scwsource_module=os.environ['SCWDATA_SOURCE_MODULE']


@pytest.mark.skip(reason="no way of testing this outside SDSC")
def test_cat():
    remote=ddosaclient.AutoRemoteDDOSA()

    req=(remote.prepare_request("CatExtract"))
    print(req)

    assert 'token' in req['params']

    product=remote.query(target="CatExtract",
                         modules=["ddosa","sdsc","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="035200230010.001")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    print("product:",product)

