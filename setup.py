from setuptools import setup
import sys


setup_requires = ['setuptools >= 41.0.1']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')

setup(
        name='ddaclient',
        version='1.1.7',
        py_modules= ['ddaclient','simple_logger'],
        package_data     = {
            "": [
                "*.txt",
                "*.md",
                "*.rst",
                "*.py"
                ]
            },
        entry_points={
                'console_scripts':[
                    'dda-client = ddaclient:main'
                ]
        },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        description="client for data-analysis services",
        long_description="",
        #long_description=open('README.md', 'rt').read(),
        )


