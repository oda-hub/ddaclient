from setuptools import setup

setup(
        name='ddaclient',
        version='1.0',
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
        long_description=open('README.md').read(),
        )
