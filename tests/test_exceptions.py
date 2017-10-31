import pytest
import requests
import os
import time
import astropy.io.fits as fits

import ddosaclient

scwsource_module="ddosa"
if 'SCWDATA_SOURCE_MODULE' in os.environ:
    scwsource_module=os.environ['SCWDATA_SOURCE_MODULE']



def test_broken_connection():
    remote=ddosaclient.RemoteDDOSA("http://127.0.1.1:1","")

    with pytest.raises(requests.ConnectionError):
        product=remote.query(target="ii_spectra_extract",
                             modules=["ddosa","git://ddosadm"],
                             assume=[scwsource_module+'.ScWData(input_scwid="035200230010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

def test_failing_request():
    remote=ddosaclient.AutoRemoteDDOSA()

    #with pytest.raises(requests.ConnectionError):

    try:
        product=remote.query(target="FailingMedia",
                             modules=["ddosa","git://ddosadm"],
                             assume=[scwsource_module+'.ScWData(input_scwid="035200250010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e, 'exceptions')
        assert len(e.exceptions) == 1
        print(e.exceptions)
        assert e.exceptions[0]['requested_by'] == '+FailingMedia.v0 output_required_by_parent +FailingMedia.v0 direct'



def test_bad_request():
    remote=ddosaclient.AutoRemoteDDOSA()

    #with pytest.raises(requests.ConnectionError):

    with pytest.raises(ddosaclient.WorkerException):
        product=remote.query(target="Undefined",
                             modules=["ddosa","git://ddosadm"],
                             assume=[scwsource_module+'.ScWData(input_scwid="035200250010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

def test_graph_exception():
    remote=ddosaclient.AutoRemoteDDOSA()

    with pytest.raises(ddosaclient.AnalysisException):
        product=remote.query(target="CatExtract",
                         modules=["ddosa","git://ddosadm"],
                         assume=['ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])



def test_handled_exception():
    remote=ddosaclient.AutoRemoteDDOSA()

    try:
        product=remote.query(target="CatExtract",
                         modules=["git://ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="935200230010.001")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e,'exceptions')
        assert len(e.exceptions)==1
        print(e.exceptions)
        assert e.exceptions[0]['node']=="ScWData"
