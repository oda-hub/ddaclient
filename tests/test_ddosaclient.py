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

test_scw=os.environ.get('TEST_SCW',"035200230010.001")


def test_cat():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="CatExtract",
                         modules=["git://ddosa"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    print(("product:",product))

def test_cat_injection():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v1"
        }
    ]

    product=remote.query(target="CatForImage",
                         modules=["git://ddosa","git://ddosadm","git://gencat"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
                         inject=[cat])

    print(("product:",product))

    d=fits.open(product.cat)[1].data
    assert cat[1]['catalog'][0]['NAME'] in d['NAME']


def test_cat_injection_image():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v0",
            "cached":False,
        }
    ]

    product=remote.query(target="ii_skyimage",
                         modules=["ddosa","git://ddosadm","git://gencat"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")',
                                 'ddosa.ii_skyimage(input_cat=gencat.CatForImage)'],
                         inject=[cat])

    print(("product:",product))

    d=fits.open(product.skyres)[2].data
    assert cat[1]['catalog'][0]['NAME'] in d['NAME']


def test_cat_injection_image_empty_cat():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                ],
            "version": "v0_empty",
             ""
            "cached":False,
        }
    ]

    product=remote.query(target="ii_skyimage",
                         modules=["ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")',
                                 ],
                         inject=[])

    print(("product:",product))

    d=fits.open(product.skyres)[2].data
    #assert len([k[] for k in d])==0

def test_cat_injection_spectra():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v1"
        }
    ]


    product=remote.query(target="ii_spectra_extract",
                         modules=["ddosa","git://ddosadm","git://gencat"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                 'ddosa.ii_spectra_extract(input_cat=gencat.CatForSpectra)',
                                ],
                         inject = [cat])

    assert os.path.exists(product.spectrum)

    print(("product:",product))

    assert hasattr(product, 'spectrum')
    d = fits.open(product.spectrum)

    assert len(d[1].data) == 2 + 1
    assert len(d[2:]) == 2 + 1

    assert d[2].header['NAME'] == cat[1]['catalog'][0]['NAME']

def test_lc():
    remote=ddosaclient.AutoRemoteDDOSA()

    product = remote.query(target="lc_pick",
                           modules=["git://ddosa", "git://ddosadm", 'git://rangequery'],
                           assume=['ddosa.LCGroups(input_scwlist=rangequery.TimeDirectionScWList)',
                    'rangequery.TimeDirectionScWList(\
                         use_coordinates=dict(RA=83,DEC=22,radius=5),\
                         use_timespan=dict(T1="2014-04-12T11:11:11",T2="2015-04-12T11:11:11"),\
                         use_max_pointings=1 \
                         )',
                               'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                               'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],

                     )


def test_cat_injection_lc_pick():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v1"
        }
    ]


    product=remote.query(target="lc_pick",
                         modules=["ddosa","git://ddosadm","git://gencat"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                 'ddosa.ii_lc_extract(input_cat=gencat.CatForSpectra)',
                                ],
                         inject = [cat])

    assert os.path.exists(product.lightcurve)

    print(("product:",product))

    assert hasattr(product, 'lightcurve')
    d = fits.open(product.lightcurve)

    assert len(d[1].data) == 2
    assert len(d[2:]) == 2

    assert d[2].header['NAME'] == cat[1]['catalog'][0]['NAME']


def test_cat_injection_lc():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v1"
        }
    ]


    product=remote.query(target="ii_lc_extract",
                         modules=["ddosa","git://ddosadm","git://gencat"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                 'ddosa.ii_lc_extract(input_cat=gencat.CatForSpectra)',
                                ],
                         inject = [cat])

    assert os.path.exists(product.lightcurve)

    print(("product:",product))

    assert hasattr(product, 'lightcurve')
    d = fits.open(product.lightcurve)

    assert len(d[1].data) == 2
    assert len(d[2:]) == 2

    assert d[2].header['NAME'] == cat[1]['catalog'][0]['NAME']

def test_gti():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ibis_gti",
                         modules=["ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])

    print(("product:",product))


def test_image():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ii_skyimage",
                         modules=["git://ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])


def test_spectrum():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="ii_spectra_extract",
                         modules=["ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                 'ddosa.CatForLC(use_minsig=3)',
                                ])

    assert os.path.exists(product.spectrum)


def test_spectrum_show_standard_catalog():
    remote=ddosaclient.AutoRemoteDDOSA()

    product=remote.query(target="CatForSpectraFromImaging",
                         modules=["ddosa","git://ddosadm"],
                         assume=[scwsource_module+'.ScWData(input_scwid="'+test_scw+'")',
                                 'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                 'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                 'ddosa.CatForLC(use_minsig=3)',
                                 'ddosa.CatForSpectraFromImaging(use_cached=True)'
                                ])

    assert os.path.exists(product.cat)

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

def test_summary_injection():
    remote=ddosaclient.AutoRemoteDDOSA()

    cat=['SourceCatalog',
             {
                "catalog": [
                        {
                            "DEC": 23,
                            "NAME": "TEST_SOURCE",
                            "RA": 83
                        },
                        {
                            "DEC": 13,
                            "NAME": "TEST_SOURCE2",
                            "RA": 83
                        }
                    ],
                "version": "v1"
            }
        ]


def test_mosaic_injection():
    remote=ddosaclient.AutoRemoteDDOSA()


    cat=['SourceCatalog',
         {
            "catalog": [
                    {
                        "DEC": 23,
                        "NAME": "TEST_SOURCE",
                        "RA": 83
                    },
                    {
                        "DEC": 13,
                        "NAME": "TEST_SOURCE2",
                        "RA": 83
                    }
                ],
            "version": "v1"
        }
    ]


    product=remote.query(target="Mosaic",
              modules=["git://ddosa","git://ddosadm","git://osahk","git://mosaic",'git://rangequery','git://gencat'],
              assume=['mosaic.ScWImageList(\
                  input_scwlist=\
                  rangequery.TimeDirectionScWList(\
                      use_coordinates=dict(RA=83,DEC=22,radius=5),\
                      use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                      use_max_pointings=2 \
                      )\
                  )\
              ',
              'mosaic.Mosaic(use_pixdivide=4)',
              'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
              'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'],
               inject=[cat])


    assert os.path.exists(product.skyima)

def test_sum_spectrum():
    remote=ddosaclient.AutoRemoteDDOSA()

    try:
        product=remote.query(target="ISGRISpectraSum",
                  modules=["ddosa","git://ddosadm","git://useresponse/cd7855bf7","git://process_isgri_spectra/2200bfd","git://rangequery"],
                  assume=['process_isgri_spectra.ScWSpectraList(\
                      input_scwlist=\
                      rangequery.TimeDirectionScWList(\
                          use_coordinates=dict(RA=83,DEC=22,radius=5),\
                          use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                          use_max_pointings=3 \
                          )\
                      )\
                  ',
                  'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                  'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
    except ddosaclient.WorkerException as e:
        if len(e.args)>2:
            print((e[2]))
        raise

    import astropy.io.fits as fits

    
    assert fits.open(product.isgri_sum_Crab)[1].header['EXPOSURE']>3000
    #assert os.path.exists(product.spectrum)


def test_sum_spectrum_extract_all():
    remote = ddosaclient.AutoRemoteDDOSA()

    try:
        product = remote.query(target="ISGRISpectraSum",
                               modules=["ddosa","git://ddosadm","git://useresponse/cd7855bf7","git://process_isgri_spectra/2200bfd",
                                        "git://rangequery"],
                               assume=['process_isgri_spectra.ScWSpectraList(\
                      input_scwlist=\
                      rangequery.TimeDirectionScWList(\
                          use_coordinates=dict(RA=83,DEC=22,radius=5),\
                          use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                          use_max_pointings=5 \
                          )\
                      )\
                  ',
                                       'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                       'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")',
                                       'process_isgri_spectra.ISGRISpectraSum(use_extract_all=True)'])
    except ddosaclient.WorkerException as e:
        if len(e.args) > 2:
            print()
            e[2]
        raise

    import astropy.io.fits as fits

    assert fits.open(product.isgri_sum_Crab)[1].header['EXPOSURE'] > 3000

@pytest.mark.skip(reason="no way of currently testing this")
def test_fit_one():
    remote=ddosaclient.AutoRemoteDDOSA()

    product = remote.query(target="FitSourcePowerlaw",
                           modules=["ddosa","git://ddosadm","git://useresponse/cd7855bf7","git://process_isgri_spectra/2200bfd","git://rangequery",
                                    "git://ddjemx","git://fit"],
                           assume=[scwsource_module + '.ScWData(input_scwid="066500330010.001")',
                                   'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                                   'ddosa.ImagingConfig(use_SouFit=0,use_DoPart2=1,use_version="soufit0_p2")',
                                   'ddosa.CatForLC(use_minsig=3)',
                                   'fit.FitSourcePowerlaw(use_sname="Crab")'
                                   ])


    print(("product:", product))

def test_report_scwlist():
    remote = ddosaclient.AutoRemoteDDOSA()

    try:
        product = remote.query(target="ReportScWList",
                               modules=["ddosa", "git://ddosadm",
                                        "git://rangequery"],
                               assume=['rangequery.ReportScWList(\
                      input_scwlist=\
                      rangequery.TimeDirectionScWList(\
                          use_coordinates=dict(RA=83,DEC=22,radius=5),\
                          use_timespan=dict(T1="2008-04-12T11:11:11",T2="2009-04-12T11:11:11"),\
                          use_max_pointings=3 \
                          )\
                      )'])

    except ddosaclient.WorkerException as e:
        if len(e.args) > 2:
            print()
            e[2]
        raise

    assert hasattr(product,'scwidlist')

    print((product.scwidlist))

    assert len(product.scwidlist)==3

    assert product.scwidlist==['072700080010.001', '072700090010.001', '072700100010.001']

