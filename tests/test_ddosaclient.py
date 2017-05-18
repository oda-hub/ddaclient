import pytest
import requests
import os

import ddosaclient

def test_AutoRemoteDDOSA_construct():
    remote=ddosaclient.AutoRemoteDDOSA()

def test_AutoRemoteDDOSA_docker():
    remote=ddosaclient.AutoRemoteDDOSA(config_version="docker_any")

def test_broken_connection():
    remote=ddosaclient.RemoteDDOSA("http://127.0.1.1:1","")

    with pytest.raises(requests.ConnectionError):
        product=remote.query(target="ii_spectra_extract",
                             modules=["ddosa","git://ddosadm"],
                             assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

def test_bad_request():
    remote=ddosaclient.AutoRemoteDDOSA()

    #with pytest.raises(requests.ConnectionError):

    with pytest.raises(ddosaclient.WorkerException):
        product=remote.query(target="Undefined",
                             modules=["ddosa","git://ddosadm"],
                             assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])



def test_image():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ii_skyimage",
                         modules=["ddosa","git://ddosadm"],
                         assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    assert os.path.exists(product.skyres)
    assert os.path.exists(product.skyima)

def test_spectrum():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ii_spectra_extract",
                         modules=["ddosa","git://ddosadm"],
                         assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    assert os.path.exists(product.spectrum)

def test_mosaic():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="Mosaic",
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


    assert os.path.exists(product.skyima)
