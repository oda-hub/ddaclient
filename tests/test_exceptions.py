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
        assert e.exceptions[0]['requested_by'] == '+FailingMedia.v0 output_required_by_parent +FailingMedia.v0 command_line'



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

def test_mosaic_exception_empty():
    remote=ddosaclient.AutoRemoteDDOSA()

    try:
        product=remote.query(target="Mosaic",
              modules=["ddosa","git://ddosadm","git://osahk","git://mosaic",'git://rangequery'],
              assume=['mosaic.ScWImageList(\
                  input_scwlist=\
                  rangequery.TimeDirectionScWList(\
                      use_coordinates=dict(RA=83,DEC=22,radius=5),\
                      use_timespan=dict(T1="2010-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                      use_max_pointings=50 \
                      )\
                  )\
              ',
              'mosaic.Mosaic(use_pixdivide=4)',
              'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
              'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e, 'exceptions')
        assert len(e.exceptions) == 1
        print(e.exceptions)
        assert e.exceptions[0]['exception']==u'EmptyScWList()'




def test_mosaic_ii_exception_empty():
    remote=ddosaclient.AutoRemoteDDOSA()

    try:
        product=remote.query(target="mosaic_ii_skyimage",
              modules=["ddosa","git://ddosadm","git://osahk","git://mosaic",'git://rangequery'],
              assume=['ddosa.ImageGroups(\
                  input_scwlist=\
                  rangequery.TimeDirectionScWList(\
                      use_coordinates=dict(RA=83,DEC=22,radius=5),\
                      use_timespan=dict(T1="2010-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                      use_max_pointings=50 \
                      )\
                  )\
              ',
              'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
              'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

        assert os.path.exists(product.skyima)

    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e, 'exceptions')
        assert len(e.exceptions) == 1
        print(e.exceptions)
        assert e.exceptions[0]['exception']==u'EmptyScWList()'




def test_sum_spectrum_empty():
    remote = ddosaclient.AutoRemoteDDOSA()

    try:
        product = remote.query(target="ISGRISpectraSum",
                               modules=["ddosa", "git://ddosadm", "git://useresponse", "git://process_isgri_spectra",
                                        "git://rangequery"],
                               assume=['process_isgri_spectra.ScWSpectraList(\
                      input_scwlist=\
                      rangequery.TimeDirectionScWList(\
                          use_coordinates=dict(RA=83,DEC=22,radius=5),\
                          use_timespan=dict(T1="2011-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                          use_max_pointings=3 \
                          )\
                      )\
                  ',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
        import astropy.io.fits as fits
        assert fits.open(product.isgri_sum_Crab)[1].header['EXPOSURE'] > 3000
        # assert os.path.exists(product.spectrum)

    except ddosaclient.WorkerException as e:
        if len(e.args) > 2:
            print(e[2])
        raise
    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e, 'exceptions')
        assert len(e.exceptions) == 1
        print(e.exceptions)
        assert e.exceptions[0]['exception']==u'EmptyScWList()'


def test_lc_pick_empty():
    remote = ddosaclient.AutoRemoteDDOSA()

    try:
        product = remote.query(target="lc_pick",
                               modules=["ddosa", "git://ddosadm", "git://useresponse", "git://process_isgri_spectra",
                                        "git://rangequery"],
                               assume=['ddosa.LCGroups(\
                      input_scwlist=\
                      rangequery.TimeDirectionScWList(\
                          use_coordinates=dict(RA=83,DEC=22,radius=5),\
                          use_timespan=dict(T1="2011-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                          use_max_pointings=3 \
                          )\
                      )\
                  ',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
        import astropy.io.fits as fits
        assert fits.open(product.isgri_sum_Crab)[1].header['EXPOSURE'] > 3000
        # assert os.path.exists(product.spectrum)

    except ddosaclient.WorkerException as e:
        if len(e.args) > 2:
            print(e[2])
        raise
    except ddosaclient.AnalysisException as e:
        print(e)
        assert hasattr(e, 'exceptions')
        assert len(e.exceptions) == 1
        print(e.exceptions)
        assert e.exceptions[0]['exception']==u'EmptyScWList()'


