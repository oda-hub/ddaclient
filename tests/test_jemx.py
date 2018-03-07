import pytest
import requests
import os
import time
import astropy.io.fits as fits

import ddosaclient

scwsource_module="ddosa"
if 'SCWDATA_SOURCE_MODULE' in os.environ:
    scwsource_module=os.environ['SCWDATA_SOURCE_MODULE']

def test_AutoRemoteDDOSA_construct():
    remote=ddosaclient.AutoRemoteDDOSA()

#def test_AutoRemoteDDOSA_docker():
#    remote=ddosaclient.AutoRemoteDDOSA(config_version="docker_any")

test_scw=os.environ.get('TEST_SCW',"010200210010.001")
test_scw_list_str=os.environ.get('TEST_SCW_LIST','["005100410010.001","005100420010.001","005100430010.001"]')


def test_single_image():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="jemx_image",
                         modules=["git://ddosa","git://ddosadm","git://ddjemx"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")'])

    assert os.path.exists(product.skyima)

def test_mosaic_osa():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="mosaic_jemx",
              modules=["git://ddosa","git://ddosadm","git://ddjemx",'git://rangequery'],
              assume=['ddjemx.JMXImageGroups(\
                  input_scwlist=\
                  ddosa.IDScWList(\
                      use_scwid_list=%s\
                      )\
                  )'%test_scw_list_str]
              )


    assert os.path.exists(product.skyima)

def test_mosaic():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="mosaic_jemx",
              modules=["git://ddosa","git://ddosadm","git://ddjemx",'git://rangequery'],
              assume=['ddjemx.JMXScWImageList(\
                  input_scwlist=\
                  ddosa.IDScWList(\
                      use_scwid_list=%s\
                      )\
                  )'%test_scw_list_str]
              )


    assert os.path.exists(product.skyima)

def test_mosaic_rangequery():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="mosaic_jemx",
              modules=["git://ddosa","git://ddosadm","git://ddjemx",'git://rangequery'],
              assume=['ddjemx.JMXScWImageList(\
                  input_scwlist=\
                  rangequery.TimeDirectionScWList(\
                      use_coordinates=dict(RA=83,DEC=22,radius=5),\
                      use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                      use_max_pointings=2 \
                      )\
                  )']
              )


    assert os.path.exists(product.skyima)

def test_spectrum_sum():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="spe_pick",
              modules=["git://ddosa","git://ddosadm","git://ddjemx",'git://rangequery'],
              assume=['ddjemx.JMXImageSpectraGroups(\
                  input_scwlist=\
                  rangequery.TimeDirectionScWList(\
                      use_coordinates=dict(RA=83,DEC=22,radius=5),\
                      use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                      use_max_pointings=2 \
                      )\
                  )']
              )


    assert os.path.exists(product.spectrum_Crab)
