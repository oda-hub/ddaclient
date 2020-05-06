from setuptools import setup

setup_requires = ['setuptools >= 30.3.0', 'setuptools-git-version']

setup(
        name='ddaclient',
        version='1.0.2-dev0',
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


if {'pytest', 'test', 'ptr'}.intersection(sys.argv):
    setup_requires.append('pytest-runner')


