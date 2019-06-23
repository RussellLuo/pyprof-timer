#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


# Manually extract the __about__
about = {}
with open('pyprof_timer/__about__.py') as f:
    exec(f.read(), about)


setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__email__'],
    maintainer=about['__author__'],
    maintainer_email=about['__email__'],
    keywords='Profiling, Timer, Python',
    description=about['__doc__'],
    license=about['__license__'],
    long_description=about['__doc__'],
    packages=find_packages(exclude=['tests']),
    url=about['__uri__'],
    install_requires=[
        'monotonic>=1.3',
        'six>=1.10.0',
        'tree-format==0.1.1',
    ],
)
