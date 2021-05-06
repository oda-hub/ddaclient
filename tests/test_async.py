import pytest
import requests
import os
import time
import random
import urllib.request
import urllib.parse
import urllib.error

import ddaclient

test_scw = os.environ.get('TEST_SCW', "010200210010.001")
test_scw_list_str = os.environ.get(
    'TEST_SCW_LIST', '["005100410010.001","005100420010.001","005100430010.001"]')

default_callback = "http://mock-dispatcher.dev:6001/callback"


def test_AutoRemoteDDA_construct():
    remote = ddaclient.AutoRemoteDDA()
    print(remote)


def test_poke():
    remote = ddaclient.AutoRemoteDDA()
    remote.poke()


@pytest.mark.skip(reason="obsolete")
def test_history():
    remote = ddaclient.AutoRemoteDDA()
    remote.query("history")


@pytest.mark.skip(reason="obsolete")
def test_poke_sleeping():
    remote = ddaclient.AutoRemoteDDA()

    import threading

    def worker():
        remote.query("sleep:10")

    t = threading.Thread(target=worker)
    t.start()

    for i in range(15):
        time.sleep(1)
        try:
            r = remote.poke()
            print(i, r)
            break
        except ddaclient.WorkerException as e:
            print(e)


@pytest.mark.verylong
def test_broken_connection():
    remote = ddaclient.RemoteDDA("http://127.0.3.1:1", "")

    with pytest.raises(requests.ConnectionError):
        product = remote.query(target="ii_spectra_extract",
                               modules=["ddosa", "git://ddosadm"],
                               assume=['ddosa.ScWData(input_scwid="185200230010.001")',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    assert product


ddosa11_modules = [
    "git://ddosa",
    "git://ddosa/staging-1-3",
    "git://findic/staging-1-3-icversion",
    "git://ddosa11/staging-1-3",
    "git://ddosa_delegate/staging-1-3",
]


def test_small_request():
    remote = ddaclient.AutoRemoteDDA()

    while True:
        try:
            product = remote.query(target="ii_skyimage",
                                modules=ddosa11_modules,
                                assume=['ddosa.ScWData(input_scwid="185200230010.001")',
                                        'ddosa.ImageBins(use_ebins=[(25,80)])',
                                        ])
            print(product)
            break
        except ddaclient.AnalysisDelegatedException as e:
            if e.delegation_state == "done":
                break
            time.sleep(1)



@pytest.mark.verylong
def test_very_large_request():
    remote = ddaclient.AutoRemoteDDA()

    with pytest.raises(requests.ConnectionError):
        product = remote.query(target="ii_spectra_extract",
                               modules=["ddosa", "git://ddosadm"],
                               assume=['ddosa.ScWData(input_scwid=[{}])'.format('035200230010.001'*2000),
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    assert product


@pytest.mark.long
def test_analysis_exception():
    remote = ddaclient.AutoRemoteDDA()

    print(remote)

    while True:
        try:
            product = remote.query(target="ibis_gti",
                                   modules=[
                                       "git://ddosa/staging-1-3", 'git://findic/staging-1-3', "git://ddosa11/staging-1-3"],
                                   assume=['ddosa.ScWData(input_scwid="335200230010.001")',
                                           'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                           'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
            break
        except ddaclient.AnalysisException as e:
            print("found as expected exception", e)
            return
        except ddaclient.AnalysisDelegatedException as e:
            print("waiting", repr(e))
            time.sleep(2)

    raise RuntimeError("should have raised exception!")


@pytest.mark.xfail
def test_bad_request():
    remote = ddaclient.AutoRemoteDDA()

    # with pytest.raises(requests.ConnectionError):

    with pytest.raises(ddaclient.WorkerException):
        product = remote.query(target="Undefined",
                               modules=["git://ddosa/staging-1-3"],
                               assume=['ddosa.ScWData(input_scwid="035200230010.001")',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])


def test_delegation():
    remote = ddaclient.AutoRemoteDDA()

    random_rev = random.randint(50, 1800)

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="ii_skyimage",
                               modules=["ddosa", "git://ddosadm"],
                               assume=['ddosa.ScWData(input_scwid="%.4i00430010.001")' % random_rev,
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                               prompt_delegate=True,
                               callback=default_callback,
                               )

    assert excinfo.value.delegation_state == "submitted"


def test_lc_delegation():
    remote = ddaclient.AutoRemoteDDA()

    random_ra = 83+(random.random()-0.5)*5

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="lc_pick",
                               modules=["git://ddosa",
                                        "git://ddosadm", 'git://rangequery'],
                               assume=['ddosa.ImageGroups(\
                         input_scwlist=\
                         rangequery.TimeDirectionScWList(\
                             use_coordinates=dict(RA=%.5lg,DEC=22,radius=5),\
                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                             use_max_pointings=1 \
                             )\
                         )\
                     )\
                 ',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                               prompt_delegate=True,
                               callback=default_callback,
                               )


def test_mosaic_delegation():
    remote = ddaclient.AutoRemoteDDA()

    random_ra = 83+(random.random()-0.5)*5

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="mosaic_ii_skyimage",
                               modules=["git://ddosa", 'git://rangequery'],
                               assume=['ddosa.ImageGroups(\
                         input_scwlist=\
                         rangequery.TimeDirectionScWList(\
                             use_coordinates=dict(RA=%.5lg,DEC=22,radius=5),\
                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                             use_max_pointings=2 \
                             )\
                         )' % random_ra,
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                               prompt_delegate=True,
                               callback="file://data/ddcache/test_callback",
                               )


def test_spectra_delegation():
    remote = ddaclient.AutoRemoteDDA()

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="ISGRISpectraSum",
                               modules=["git://ddosa",
                                        "git://ddosadm", 'git://rangequery'],
                               assume=['process_isgri_spectra.ScWSpectraList(\
                         input_scwlist=\
                         rangequery.TimeDirectionScWList(\
                             use_coordinates=dict(RA=83,DEC=22,radius=5),\
                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                             use_max_pointings=6 \
                             )\
                         )',
                                       'ddosa.ImageBins(use_ebins=[(20,80)],use_autoversion=True)',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                               prompt_delegate=True,
                               callback=default_callback,
                               )

    assert excinfo.value.delegation_state == "submitted"


def test_mosaic_delegation_cat():
    remote = ddaclient.AutoRemoteDDA()

    random_ra = 83+(random.random()-0.5)*5
    cat = ['SourceCatalog',
           {
               "catalog": [
                   {
                       "DEC": 23,
                       "NAME": "TEST_SOURCE1",
                       "RA": 83
                   },
                   {
                       "DEC": 13,
                       "NAME": "TEST_SOURCE2",
                       "RA": random_ra
                   }
               ],
               "version": "v1"
           }
           ]

    job_id = time.strftime("%y%m%d_%H%M%S")
    encoded = urllib.parse.urlencode(
        dict(job_id=job_id, session_id="test_mosaic"))

    print(("encoded:", encoded))

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="mosaic_ii_skyimage",
                               modules=["git://ddosa", "git://ddosadm",
                                        'git://rangequery', 'git://gencat'],
                               assume=['ddosa.ImageGroups(\
                         input_scwlist=\
                         rangequery.TimeDirectionScWList(\
                             use_coordinates=dict(RA=83,DEC=22,radius=5),\
                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                             use_max_pointings=100 \
                             )\
                         )\
                     ',
                                       'ddosa.ImageBins(use_ebins=[(20,80)],use_autoversion=True)',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                               callback=default_callback+"?"+encoded,
                               prompt_delegate=True,
                               inject=[cat],
                               )
        # callback="http://intggcn01:5000/callback?job_id=1&asdsd=2",

    assert excinfo.value.delegation_state == "submitted"


def test_spectra_delegation_cat_distribute():
    remote = ddaclient.AutoRemoteDDA()

    random_ra = 83+(random.random()-0.5)*5
    cat = ['SourceCatalog',
           {
               "catalog": [
                   {
                       "DEC": 23,
                       "NAME": "TEST_SOURCE1",
                       "RA": 83
                   },
                   {
                       "DEC": 13,
                       "NAME": "TEST_SOURCE2",
                       "RA": random_ra
                   }
               ],
               "version": "v1"
           }
           ]

    job_id = time.strftime("%y%m%d_%H%M%S")
    encoded = urllib.parse.urlencode(
        dict(job_id=job_id, session_id="test_mosaic"))

    print(("encoded:", encoded))

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="ISGRISpectraSum",
                               modules=["git://ddosa", 'git://rangequery', "git://useresponse/cd7855bf7",
                                        "git://process_isgri_spectra/2200bfd", 'git://gencat', 'git://ddosa_delegate'],
                               assume=['process_isgri_spectra.ScWSpectraList(input_scwlist=rangequery.TimeDirectionScWList)',
                                       'rangequery.TimeDirectionScWList(\
                                             use_coordinates=dict(RA=83,DEC=22,radius=5),\
                                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                                             use_max_pointings=10 \
                                        )',
                                       'ddosa.ImageBins(use_ebins=[(20,80)],use_autoversion=True)',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                               callback=default_callback+"?"+encoded,
                               prompt_delegate=True,
                               inject=[cat],
                               )
        # callback="http://intggcn01:5000/callback?job_id=1&asdsd=2",

    assert excinfo.value.delegation_state == "submitted"


def test_mosaic_delegation_cat_distribute():
    remote = ddaclient.AutoRemoteDDA()

    random_ra = 83+(random.random()-0.5)*5
    cat = ['SourceCatalog',
           {
               "catalog": [
                   {
                       "DEC": 23,
                       "NAME": "TEST_SOURCE1",
                       "RA": 83
                   },
                   {
                       "DEC": 13,
                       "NAME": "TEST_SOURCE2",
                       "RA": random_ra
                   }
               ],
               "version": "v1"
           }
           ]

    job_id = time.strftime("%y%m%d_%H%M%S")
    encoded = urllib.parse.urlencode(
        dict(job_id=job_id, session_id="test_mosaic"))

    print(("encoded:", encoded))

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="mosaic_ii_skyimage",
                               modules=["git://ddosa", 'git://rangequery',
                                        'git://gencat/dev', 'git://ddosa_delegate'],
                               assume=['ddosa.ImageGroups(input_scwlist=rangequery.TimeDirectionScWList)',
                                       'rangequery.TimeDirectionScWList(\
                                             use_coordinates=dict(RA=83,DEC=22,radius=5),\
                                             use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                                             use_max_pointings=10 \
                                        )',
                                       'ddosa.ImageBins(use_ebins=[(20,80)],use_autoversion=True)',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                               callback=default_callback+"?"+encoded,
                               prompt_delegate=True,
                               inject=[cat],
                               )
        # callback="http://intggcn01:5000/callback?job_id=1&asdsd=2",

    assert excinfo.value.delegation_state == "submitted"


def test_jemx():
    remote = ddaclient.AutoRemoteDDA()

 #   random_ra=83+(random.random()-0.5)*5

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="mosaic_jemx",
                               modules=["git://ddosa", "git://ddosadm",
                                        "git://ddjemx", 'git://rangequery'],
                               assume=['ddjemx.JMXScWImageList(\
                    input_scwlist=\
                    ddosa.IDScWList(\
                        use_scwid_list=%s\
                        )\
                    )' % test_scw_list_str],
                               prompt_delegate=True,
                               )

        #assert os.path.exists(product.spectrum_Crab)


def test_jemx_osa_mosaic():
    remote = ddaclient.AutoRemoteDDA()

 #   random_ra=83+(random.random()-0.5)*5

    with pytest.raises(ddaclient.AnalysisDelegatedException) as excinfo:
        product = remote.query(target="mosaic_jemx",
                               modules=["git://ddosa", "git://ddosadm",
                                        "git://ddjemx", 'git://rangequery'],
                               assume=['ddjemx.JMXImageGroups(\
                    input_scwlist=\
                    ddosa.IDScWList(\
                        use_scwid_list=%s\
                        )\
                    )' % test_scw_list_str],
                               prompt_delegate=True,
                               )

        #assert os.path.exists(product.spectrum_Crab)
