#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='requests_httpsproxy',
    version='1.0.1',
    description='allow http/https requests through https proxy',
    author='Phus Lu',
    author_email='phuslu@hotmail.com',
    url='https://github.com/phuslu/requests_httpsproxy',
    packages=find_packages(),
    zip_safe=True,
    include_package_data=True,
    license='MIT',
    platforms='any',
    install_requires=['requests>=2.13.0', 'pyOpenSSL>=0.11', 'tlslite-ng'],
)
