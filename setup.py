#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


def get_info(name):
    basedir = os.path.dirname(__file__)
    with open(os.path.join(basedir, 'pyprof_timer/__info__.py')) as f:
        locals = {}
        exec(f.read(), locals)
        return locals[name]


setup(
    name='pyprof-timer',
    version=get_info('__version__'),
    author=get_info('__author__'),
    author_email=get_info('__email__'),
    maintainer=get_info('__author__'),
    maintainer_email=get_info('__email__'),
    keywords='Profiling, Timer, Python',
    description=get_info('__doc__'),
    license=get_info('__license__'),
    long_description=get_info('__doc__'),
    packages=find_packages(exclude=['tests']),
    url='https://github.com/RussellLuo/pyprof-timer',
    install_requires=[
        'monotonic==1.3',
        'six==1.10.0',
        'tree-format==0.1.1',
    ],
)
