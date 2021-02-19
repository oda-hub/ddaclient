# ddaclient

note that the password is stored in .secret-ddosa-clienet and should be put in the home directory

example calling from shell:

```bash
INTEGRAL_DDCACHE_ROOT=/data/ddcache/ \
DDOSA_WORKER_URL=http://strasbourg.odahub.io \
    dda-client 
        ii_skyimage \
        -m git://ddosa \
        -m git://ddosadm \
        -a 'ddosadm.ScWData(input_scwid="066500250010.001")'
```

or from python:

```python
import ddaclient

remote=ddaclient.AutoRemoteDDOSA()

product=remote.query(target="ii_skyimage",
                     modules=["git://ddosa","git://ddosadm"],
                     assume=['ddosadm.ScWData(input_scwid="066500250010.001")',
                             'ddosa.ImageBins(use_ebins=[(20,40)],use_version="onebin_20_40")',
                             'ddosa.ImagingConfig(use_SouFit=0,use_version="soufit0")'])
```
