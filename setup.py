from distutils.core import setup

setup(
        name='ddosa-client',
        version='1.0',
        py_modules= ['ddosaclient','simple_logger','discover_docker'],
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
                    'dda-client = ddosaclient:main'
                ]
        },
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),
        )
