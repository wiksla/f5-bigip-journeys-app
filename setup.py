
from setuptools import setup, find_packages

setup(
    name='migrate',
    version='0.1',
    py_modules=['migrate'],
    include_package_data=True,
    packages=find_packages(include=['utils.*', 'parser.*', 'modifier.*']),
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        migrate=migrate:cli
    ''',
)
