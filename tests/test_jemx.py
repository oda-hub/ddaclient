import pytest
import requests
import os
import time
import urllib.request, urllib.parse, urllib.error
import astropy.io.fits as fits

import ddaclient

pytestmark = pytest.mark.skip(reason="only async testing makes sense")

scwsource_module="ddosa"
if 'SCWDATA_SOURCE_MODULE' in os.environ:
    scwsource_module=os.environ['SCWDATA_SOURCE_MODULE']

def test_AutoRemoteDDOSA_construct():
    remote=ddaclient.AutoRemoteDDOSA()

#def test_AutoRemoteDDOSA_docker():
#    remote=ddaclient.AutoRemoteDDOSA(config_version="docker_any")

test_scw=os.environ.get('TEST_SCW',"010200210010.001")
test_scw_list_str=os.environ.get('TEST_SCW_LIST','["005100410010.001","005100420010.001","005100430010.001"]')


def test_single_image():
    remote=ddaclient.AutoRemoteDDOSA()

    product=remote.query(target="jemx_image",
                         modules=["git://ddosa","git://ddosadm","git://ddjemx"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")'])

    assert os.path.exists(product.skyima)

def test_mosaic_osa():
    remote=ddaclient.AutoRemoteDDOSA()

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
    remote=ddaclient.AutoRemoteDDOSA()

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
    remote=ddaclient.AutoRemoteDDOSA()

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
    remote=ddaclient.AutoRemoteDDOSA()

    custom_version=time.strftime("%Y%m%d_%H%M%S")

    kwargs=dict(
              target="spe_pick",
              modules=["git://ddosa","git://ddjemx",'git://rangequery'],
              assume=['ddjemx.JMXImageSpectraGroups(input_scwlist=rangequery.TimeDirectionScWList)',
                      'rangequery.TimeDirectionScWList(\
                              use_coordinates=dict(RA=83,DEC=22,radius=5),\
                              use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                              use_max_pointings=1 \
                          )',
                      'ddjemx.JEnergyBins(use_version="%s",use_bins=[(5,20)])'%custom_version],
              callback='http://mock-dispatcher?'+urllib.parse.urlencode(dict(job_id=custom_version,session_id="test_jemx")),
              prompt_delegate=True,
            )

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product=remote.query(**kwargs)

    assert excinfo.value.delegation_state == "submitted"

    while True:
        time.sleep(5)

        try:
            product = remote.query(**kwargs)
        except ddaclient.AnalysisDelegatedException as e:
            print(("state:",e.delegation_state))
        except ddaclient.WorkerException:
            print(("worker exception:",e.__class__))
            break
        except Exception as e:
            print(("undefined failure:",e.__class__,e))
            raise
        else:
            print(("DONE:",product))
            break


    product=remote.query(**kwargs)


    assert os.path.exists(product.spectrum_Crab)
