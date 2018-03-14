# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='pinterest-client',
    version='1.0.2',
    author='Hau Van',
    author_email='cvhau.tt@gmail.com',
    description='A simple python client for Pinterest that support user interact with Pinterest such as simple browser.',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable', 
        'Intended Audience :: Developers', 
        'License :: OSI Approved :: MIT License', 
        'Programming Language :: Python :: 2.7'],
    install_requires=['requests', 'requests_toolbelt'],
    license="MIT",
    keywords=['Python Pinterest Client', 'Python Pinterest API'],
    url='https://github.com/cvhau/pinterest-client',
    packages=find_packages(),
    zip_safe=True)
