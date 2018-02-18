import pytest
import requests
import os
import time

import ddosaclient

def test_AutoRemoteDDOSA_construct():
    remote=ddosaclient.AutoRemoteDDOSA()

def test_AutoRemoteDDOSA_docker():
    remote=ddosaclient.AutoRemoteDDOSA(config_version="docker_any")

def test_poke():
    remote=ddosaclient.AutoRemoteDDOSA()
    remote.poke()

def test_sleep():
    remote=ddosaclient.AutoRemoteDDOSA()
    remote.query("sleep:5")

def test_history():
    remote=ddosaclient.AutoRemoteDDOSA()
    remote.query("history")

def test_poke_sleeping():
    remote=ddosaclient.AutoRemoteDDOSA()
    
    import threading
    
    def worker():
        remote.query("sleep:10")

    t = threading.Thread(target=worker)
    t.start()

    for i in range(15):
        time.sleep(1)
        try:
            r=remote.poke()
            print r
            break
        except ddosaclient.WorkerException as e:
            print e

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


def test_poke_image():
    remote=ddosaclient.AutoRemoteDDOSA()
    
    import threading
    
    def worker():
        product=remote.query(target="ii_skyimage",
                             modules=["ddosa","git://ddosadm"],
                             assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                     'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                     'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
        assert os.path.exists(product.skyres)
        assert os.path.exists(product.skyima)

    t = threading.Thread(target=worker)
    t.start()

    for i in range(15):
        time.sleep(1)
        try:
            r=remote.poke()
            print r
            break
        except ddosaclient.WorkerException as e:
            print e

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

def test_delegation():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ii_skyimage",
                         modules=["ddosa","git://ddosadm"],
                         assume=['ddosa.ScWData(input_scwid="035200430010.001")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                         prompt_delegate=True,
                         callback="http://10.25.64.51:5000/callback/1/1",
                         )

def test_mosaic_delegation():
    remote=ddosaclient.AutoRemoteDDOSA()

    product = remote.query(target="mosaic_ii_skyimage",
                           modules=["git://ddosa", "git://ddosadm", 'git://rangequery'],
                           assume=['ddosa.ImageGroups(\
                     input_scwlist=\
                     rangequery.TimeDirectionScWList(\
                         use_coordinates=dict(RA=83,DEC=22,radius=5),\
                         use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                         use_max_pointings=6 \
                         )\
                     )\
                 ',
                                   'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                   'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                            prompt_delegate=True,
                            callback="http://10.25.64.51:5000/callback/1/1",
                         )

def test_spectra_delegation():
    remote=ddosaclient.AutoRemoteDDOSA()

    product = remote.query(target="ISGRISpectraSum",
                           modules=["git://ddosa", "git://ddosadm", 'git://rangequery'],
                           assume=['process_isgri_spectra.ScWSpectraList(\
                     input_scwlist=\
                     rangequery.TimeDirectionScWList(\
                         use_coordinates=dict(RA=83,DEC=22,radius=5),\
                         use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                         use_max_pointings=6 \
                         )\
                     )\
                 ',
                                   'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                   'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                            prompt_delegate=True,
                            callback="http://10.25.64.51:5000/callback/1/1",
                         )
