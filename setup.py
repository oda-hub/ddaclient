from setuptools import setup
import sys


setup_requires = ['setuptools >= 30.3.0', 'setuptools-git-version']
if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')



setup(
        name='ddaclient',
        version='1.0.2',
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
        long_description=open('README.md').read(),
        )


